"""Momentos calculados pelo motor de trânsitos contra valores publicados (NASA/IMCCE)."""

from datetime import UTC, date, datetime, timedelta

import pytest

from arquivo.natal.chart import NatalChart, calculate_chart
from arquivo.natal.settings import AspectKind, Body, Zodiac
from arquivo.transits.engine import (
    MAX_REVELATIONS,
    EventKind,
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
    for revelation in sky.revelations:
        if revelation.transit:
            t = revelation.transit
            assert t.orb is not None and t.orb <= t.allowed_orb + 1e-6
        else:
            assert revelation.event is not None
            assert sky.day_starts <= revelation.event.at < sky.day_ends
    assert all(t.starts is not None and t.starts >= sky.day_ends for t in sky.upcoming)


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
