"""Momentos calculados pelo motor de trânsitos contra valores publicados (NASA/IMCCE)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from arquivo.natal.chart import NatalChart, calculate_chart, ecliptic_positions
from arquivo.natal.settings import AspectKind, Body, Sign, Zodiac
from arquivo.transits.engine import (
    ASPECT_WEIGHT,
    BODY_WEIGHT,
    MAX_REVELATIONS,
    Angle,
    EventKind,
    Factor,
    SkyEvent,
    Transit,
    _exact_roots,
    _group_factors,
    _moon_sign_ingresses,
    _natal_points,
    _Sky,
    _sky_aspects,
    _specificity_multiplier,
    daily_sky,
    find_events,
    find_transits,
    to_jd,
)

CHART = calculate_chart(datetime(1990, 5, 10, 13, 30, tzinfo=UTC), 38.72, -9.14)


def _close(actual: datetime, expected: datetime, minutes: float) -> None:
    assert abs(actual - expected) <= timedelta(minutes=minutes), (actual, expected)


def _events(start: datetime, end: datetime) -> list:  # type: ignore[type-arg]
    return find_events(CHART, to_jd(start), to_jd(end))


def _with_sun_at(longitude: float) -> NatalChart:
    bodies = [
        b.model_copy(update={"longitude": longitude}) if b.body is Body.SUN else b
        for b in CHART.bodies
    ]
    return CHART.model_copy(update={"bodies": bodies})


def test_exact_transit_matches_equinox() -> None:
    chart = _with_sun_at(0.0)
    found = [
        t
        for t in find_transits(
            chart,
            to_jd(datetime(2024, 3, 19, tzinfo=UTC)),
            to_jd(datetime(2024, 3, 21, tzinfo=UTC)),
        )
        if t.body is Body.SUN and t.natal_point is Body.SUN and t.kind is AspectKind.CONJUNCTION
    ]
    assert len(found) == 1
    _close(found[0].exact[0], datetime(2024, 3, 20, 3, 6, tzinfo=UTC), 2)
    assert found[0].starts is not None and found[0].ends is not None
    assert found[0].starts < found[0].exact[0] < found[0].ends


@pytest.mark.parametrize(
    ("kind", "expected", "minutes"),
    [
        (EventKind.NEW_MOON, datetime(2024, 4, 8, 18, 21, tzinfo=UTC), 2),
        (EventKind.FULL_MOON, datetime(2024, 3, 25, 7, 0, tzinfo=UTC), 2),
        (EventKind.SOLAR_ECLIPSE, datetime(2024, 4, 8, 18, 17, tzinfo=UTC), 3),
        (EventKind.LUNAR_ECLIPSE, datetime(2024, 3, 25, 7, 13, tzinfo=UTC), 3),
        (EventKind.STATION_RETROGRADE, datetime(2024, 4, 1, 22, 14, tzinfo=UTC), 30),
        (EventKind.STATION_DIRECT, datetime(2024, 4, 25, 12, 54, tzinfo=UTC), 30),
    ],
)
def test_events_match_published_times(kind: EventKind, expected: datetime, minutes: float) -> None:
    events = _events(datetime(2024, 3, 21, tzinfo=UTC), datetime(2024, 4, 28, tzinfo=UTC))
    matches = [
        e
        for e in events
        if e.kind is kind
        and (
            kind not in (EventKind.STATION_RETROGRADE, EventKind.STATION_DIRECT)
            or e.body is Body.MERCURY
        )
    ]
    assert any(abs(e.at - expected) <= timedelta(minutes=minutes) for e in matches), matches


def test_eclipse_types_and_sign_ingress() -> None:
    events = _events(datetime(2026, 8, 10, tzinfo=UTC), datetime(2026, 8, 14, tzinfo=UTC))
    eclipse = next(e for e in events if e.kind is EventKind.SOLAR_ECLIPSE)
    assert eclipse.eclipse_type == "total"
    _close(eclipse.at, datetime(2026, 8, 12, 17, 46, tzinfo=UTC), 3)
    spring = _events(datetime(2024, 3, 19, tzinfo=UTC), datetime(2024, 3, 21, tzinfo=UTC))
    ingress = next(e for e in spring if e.kind is EventKind.SIGN_INGRESS and e.body is Body.SUN)
    assert ingress.sign == "aries"
    _close(ingress.at, datetime(2024, 3, 20, 3, 6, tzinfo=UTC), 2)


def test_daily_sky_uses_only_real_events() -> None:
    sky = daily_sky(CHART, date(2026, 11, 12), "Europe/Lisbon")
    assert 0 < len(sky.revelations) <= MAX_REVELATIONS
    weights = [r.weight for r in sky.revelations]
    assert weights == sorted(weights, reverse=True)
    assert all(len(revelation.supporting) <= 3 for revelation in sky.revelations)
    for revelation in sky.revelations:
        if revelation.transit:
            t = revelation.transit
            assert t.orb is not None and t.orb <= t.allowed_orb + 1e-6
        for event in [
            revelation.event,
            *(factor.event for factor in revelation.supporting),
        ]:
            if event is not None:
                assert sky.day_starts <= event.at < sky.day_ends
    assert all(t.starts is not None and t.starts >= sky.day_ends for t in sky.upcoming)
    assert all(
        event.kind not in {EventKind.MOON_SIGN_INGRESS, EventKind.SKY_ASPECT}
        for event in sky.events
    )


def test_daily_revelations_group_transits_by_focal_point() -> None:
    sky = daily_sky(CHART, date(2026, 11, 14), "Europe/Lisbon")
    midheaven = next(
        revelation for revelation in sky.revelations if revelation.focus is Angle.MIDHEAVEN
    )
    assert midheaven.transit is not None
    factors = [
        (midheaven.transit, None),
        *((factor.transit, factor.event) for factor in midheaven.supporting),
    ]
    transit_keys = {
        (transit.body, transit.natal_point, transit.kind)
        for transit, _ in factors
        if transit is not None
    }
    pluto_trine = (Body.PLUTO, Angle.MIDHEAVEN, AspectKind.TRINE)
    uranus_conjunction = (Body.URANUS, Angle.MIDHEAVEN, AspectKind.CONJUNCTION)
    main_key = (midheaven.transit.body, midheaven.transit.natal_point, midheaven.transit.kind)
    assert main_key in {pluto_trine, uranus_conjunction}
    assert (pluto_trine if main_key == uranus_conjunction else uranus_conjunction) in transit_keys
    assert len(midheaven.supporting) <= 3

    focuses = [revelation.focus for revelation in sky.revelations if revelation.focus is not None]
    assert len(focuses) == len(set(focuses))
    factors = [
        factor
        for revelation in sky.revelations
        for factor in [
            (revelation.transit, revelation.event),
            *((item.transit, item.event) for item in revelation.supporting),
        ]
    ]
    factor_keys: list[tuple[object, ...]] = []
    for transit, event in factors:
        if transit is not None:
            factor_keys.append(("transit", transit.body, transit.natal_point, transit.kind))
        else:
            assert event is not None
            factor_keys.append(
                ("event", event.kind, event.body, event.other_body, event.aspect, event.at)
            )
    assert len(factor_keys) == len(set(factor_keys))


def test_sky_aspect_events_are_bisected_to_the_aspect_angle() -> None:
    start = to_jd(datetime(2026, 11, 14, tzinfo=UTC))
    end = to_jd(datetime(2027, 2, 12, tzinfo=UTC))
    events = _sky_aspects(_Sky(start, end, None), _natal_points(CHART))
    assert events
    event = events[0]
    assert start <= to_jd(event.at) < end
    assert event.kind is EventKind.SKY_ASPECT
    assert event.other_body is not None and event.aspect is not None
    assert event.body not in {Body.MOON, Body.NORTH_NODE, Body.CHIRON}
    assert event.other_body not in {Body.MOON, Body.NORTH_NODE, Body.CHIRON}
    assert list(Body).index(event.body) < list(Body).index(event.other_body)
    longitude = ecliptic_positions([to_jd(event.at)], event.body)[0][0]
    other_longitude = ecliptic_positions([to_jd(event.at)], event.other_body)[0][0]
    separation = abs((longitude - other_longitude + 180) % 360 - 180)
    assert (
        min(abs(separation - event.aspect.angle), abs(separation - (360 - event.aspect.angle)))
        < 0.05
    )
    assert event.sign is Sign.of(longitude)
    assert len(event.contacts) == len(set(event.contacts))
    natal_points = _natal_points(CHART)
    for contact in event.contacts:
        natal_longitude = natal_points[contact]
        distance = min(
            abs((longitude - natal_longitude + 180) % 360 - 180),
            abs((other_longitude - natal_longitude + 180) % 360 - 180),
        )
        assert distance <= 1.0
    assert event.weight == (
        (BODY_WEIGHT[event.body] + BODY_WEIGHT[event.other_body])
        / 2
        * ASPECT_WEIGHT[event.aspect]
        * 0.5
        + (1.0 if event.contacts else 0.0)
    )


def test_aspect_root_helper_ignores_wrap_discontinuity() -> None:
    assert _exact_roots([0.0, 1.0], [179.0, -179.0], lambda jd: 179 - 358 * jd) == []


def test_group_weight_uses_all_factors_and_exposes_at_most_three_supporting() -> None:
    factors = [
        Factor(
            weight=weight,
            transit=Transit(
                body=body,
                natal_point=Angle.MIDHEAVEN,
                kind=AspectKind.CONJUNCTION,
                allowed_orb=1,
                starts=None,
                ends=None,
                exact=[],
                natal_house=10,
            ),
        )
        for body, weight in zip(
            (Body.SATURN, Body.JUPITER, Body.MARS, Body.VENUS, Body.MERCURY),
            (10.123456, 9.234567, 8.123456, 7.456789, 6.345678),
            strict=True,
        )
    ]
    [revelation] = _group_factors(factors)
    assert revelation.weight == 25.7037
    assert [factor.weight for factor in revelation.supporting] == [9.234567, 8.123456, 7.456789]


def test_event_contacts_group_by_first_point_and_unfocused_events_stay_separate() -> None:
    instant = datetime(2026, 11, 14, 12, tzinfo=UTC)
    contacts = [Angle.MIDHEAVEN]
    factors = [
        Factor(
            weight=2,
            event=SkyEvent(
                kind=EventKind.SIGN_INGRESS,
                at=instant,
                body=Body.MARS,
                contacts=contacts,
            ),
        ),
        Factor(
            weight=1,
            event=SkyEvent(
                kind=EventKind.NEW_MOON,
                at=instant + timedelta(hours=1),
                body=Body.MOON,
                contacts=contacts,
            ),
        ),
        Factor(
            weight=0.5,
            event=SkyEvent(
                kind=EventKind.STATION_DIRECT,
                at=instant + timedelta(hours=2),
                body=Body.MERCURY,
            ),
        ),
        Factor(
            weight=0.25,
            event=SkyEvent(
                kind=EventKind.FULL_MOON,
                at=instant + timedelta(hours=3),
                body=Body.MOON,
            ),
        ),
    ]
    conclusions = _group_factors(factors)
    grouped = next(item for item in conclusions if item.focus is Angle.MIDHEAVEN)
    assert grouped.weight == 2.5
    assert grouped.event is not None and grouped.event.kind is EventKind.SIGN_INGRESS
    assert len(grouped.supporting) == 1
    unfocused = [item for item in conclusions if item.focus is None]
    assert len(unfocused) == 2
    assert all(not item.supporting for item in unfocused)


def test_moon_sign_ingress_has_the_entered_sign_and_is_in_window() -> None:
    events = []
    start = end = 0.0
    for offset in range(5):
        start = to_jd(datetime(2026, 11, 14, tzinfo=UTC) + timedelta(days=offset))
        end = start + 2
        events = _moon_sign_ingresses(
            _Sky(start, end, None), [house.longitude for house in CHART.houses]
        )
        if events:
            break
    assert events
    event = events[0]
    assert event.kind is EventKind.MOON_SIGN_INGRESS
    assert event.weight == 1.8
    assert start <= to_jd(event.at) < end
    longitude = ecliptic_positions([to_jd(event.at + timedelta(minutes=1))], Body.MOON)[0][0]
    assert Sign.of(longitude) is event.sign


@pytest.mark.parametrize(
    ("body", "starts", "ends", "exact", "expected"),
    [
        (Body.SATURN, None, None, [datetime(2026, 11, 14, 12, tzinfo=UTC)], 1.5),
        (Body.SATURN, datetime(2026, 11, 14, 8, tzinfo=UTC), None, [], 1.2),
        (Body.SATURN, None, datetime(2026, 11, 14, 22, tzinfo=UTC), [], 1.2),
        (Body.SATURN, None, None, [], 0.55),
        (Body.MARS, None, None, [], 1.0),
        (Body.MOON, None, None, [], 1.0),
    ],
)
def test_transit_specificity_multiplier(
    body: Body,
    starts: datetime | None,
    ends: datetime | None,
    exact: list[datetime],
    expected: float,
) -> None:
    transit = Transit(
        body=body,
        natal_point=Angle.MIDHEAVEN,
        kind=AspectKind.TRINE,
        allowed_orb=1,
        starts=starts,
        ends=ends,
        exact=exact,
        natal_house=10,
    )
    assert (
        _specificity_multiplier(
            transit,
            datetime(2026, 11, 14, tzinfo=UTC),
            datetime(2026, 11, 15, tzinfo=UTC),
        )
        == expected
    )


def test_quiet_day_gives_fewer_revelations_not_invented_ones() -> None:
    chart = CHART.model_copy(update={"bodies": CHART.bodies[:1]})
    sky = daily_sky(chart, date(2026, 11, 12), "Europe/Lisbon")
    for revelation in sky.revelations:
        assert revelation.transit is None or revelation.transit.natal_point in (
            Body.SUN,
            "ascendant",
            "midheaven",
        )


def test_lunation_just_outside_the_window_is_not_reported() -> None:
    # Lua Nova de 8/4/2024 às 18:21 UTC; uma janela de 10 min antes não a pode incluir.
    events = find_events(
        CHART,
        to_jd(datetime(2024, 4, 8, 18, 0, tzinfo=UTC)),
        to_jd(datetime(2024, 4, 8, 18, 10, tzinfo=UTC)),
    )
    assert not [e for e in events if e.kind in (EventKind.NEW_MOON, EventKind.FULL_MOON)]


def test_missing_body_ephemeris_does_not_break_daily_sky(tmp_path) -> None:  # type: ignore[no-untyped-def]
    # Sem o ficheiro de Quíron, os restantes corpos continuam a ser calculados (fallback Moshier).
    sky = daily_sky(CHART, date(2026, 11, 12), "Europe/Lisbon", ephemeris_dir=tmp_path)
    bodies = {t.body for t in sky.active} | {r.transit.body for r in sky.revelations if r.transit}
    assert Body.CHIRON not in bodies


def test_daily_sky_rejects_sideral_or_mean_node() -> None:
    from arquivo.natal.settings import Ayanamsa

    settings = CHART.settings.model_copy(
        update={"zodiac": Zodiac.SIDEREAL, "ayanamsa": Ayanamsa.LAHIRI}
    )
    chart = CHART.model_copy(update={"settings": settings})
    with pytest.raises(ValueError, match="trânsitos"):
        daily_sky(chart, date(2026, 11, 12), "Europe/Lisbon")
