"""Motor de trânsitos: o céu de cada dia sobre o mapa natal (D-028).

Tudo é cálculo determinístico com a Swiss Ephemeris: posições, momentos exatos (por bissecção, à
precisão de cerca de um minuto), entradas em signos e casas, estações, lunações e eclipses. As
orbes e os pesos de importância são convenções astrológicas e ficam registados com o resultado.
O dia juliano é tratado como UTC (a diferença para UT1 é inferior a um segundo).
"""

import math
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from enum import StrEnum
from itertools import combinations, pairwise
from pathlib import Path
from typing import Self
from zoneinfo import ZoneInfo

import swisseph as swe
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from arquivo.natal.chart import NatalChart, ecliptic_positions, house_of
from arquivo.natal.ephemeris import SWISSEPH_VERSION
from arquivo.natal.settings import MAJOR_ASPECTS, AspectKind, Body, NodeType, Sign, Zodiac
from arquivo.transits.constants import MAX_REVELATIONS as MAX_REVELATIONS

_J2000 = 2451545.0
_EPOCH = datetime(2000, 1, 1, 12, tzinfo=UTC)
_MINUTE = 1 / 1440

FAST = (Body.SUN, Body.MERCURY, Body.VENUS, Body.MARS)
TRANSIT_ORBS: dict[Body, float] = {Body.MOON: 3.0} | dict.fromkeys(FAST, 2.0)
DEFAULT_SLOW_ORB = 1.0
BODY_WEIGHT: dict[Body, float] = {
    Body.PLUTO: 5.0,
    Body.NEPTUNE: 5.0,
    Body.URANUS: 5.0,
    Body.SATURN: 4.5,
    Body.JUPITER: 4.0,
    Body.CHIRON: 3.0,
    Body.NORTH_NODE: 3.0,
    Body.MARS: 3.0,
    Body.SUN: 3.0,
    Body.VENUS: 2.5,
    Body.MERCURY: 2.5,
    Body.MOON: 1.5,
}
ASPECT_WEIGHT: dict[AspectKind, float] = {
    AspectKind.CONJUNCTION: 1.0,
    AspectKind.OPPOSITION: 0.9,
    AspectKind.SQUARE: 0.9,
    AspectKind.TRINE: 0.7,
    AspectKind.SEXTILE: 0.6,
}
_STEP = {Body.MOON: 0.25, **dict.fromkeys(FAST, 1.0), Body.NORTH_NODE: 1.0}
_HORIZON = {Body.MOON: 3.0, **dict.fromkeys(FAST, 90.0)}
LUNATION_CONTACT_ORB = 3.0
UPCOMING_DAYS = 30


class Angle(StrEnum):
    ASCENDANT = "ascendant"
    MIDHEAVEN = "midheaven"


class EventKind(StrEnum):
    SIGN_INGRESS = "sign_ingress"
    HOUSE_INGRESS = "house_ingress"
    MOON_SIGN_INGRESS = "moon_sign_ingress"
    SKY_ASPECT = "sky_aspect"
    STATION_RETROGRADE = "station_retrograde"
    STATION_DIRECT = "station_direct"
    NEW_MOON = "new_moon"
    FULL_MOON = "full_moon"
    SOLAR_ECLIPSE = "solar_eclipse"
    LUNAR_ECLIPSE = "lunar_eclipse"


class Transit(BaseModel):
    """Um planeta em trânsito em aspeto a um ponto do mapa natal, enquanto está dentro da orbe."""

    model_config = ConfigDict(frozen=True)

    body: Body
    natal_point: Body | Angle
    kind: AspectKind
    allowed_orb: float
    starts: AwareDatetime | None
    ends: AwareDatetime | None
    exact: list[AwareDatetime]
    orb: float | None = None
    applying: bool | None = None
    natal_house: int
    weight: float = 0.0


class SkyEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: EventKind
    at: AwareDatetime
    body: Body
    sign: Sign | None = None
    natal_house: int | None = None
    eclipse_type: str | None = None
    other_body: Body | None = None
    aspect: AspectKind | None = None
    contacts: list[Body | Angle] = []
    weight: float = 0.0


class Factor(BaseModel):
    model_config = ConfigDict(frozen=True)

    weight: float
    transit: Transit | None = None
    event: SkyEvent | None = None


class Revelation(BaseModel):
    model_config = ConfigDict(frozen=True)

    weight: float
    transit: Transit | None = None
    event: SkyEvent | None = None
    focus: Body | Angle | None = None
    supporting: list[Factor] = Field(default_factory=list)

    @model_validator(mode="after")
    def _one_main_factor(self) -> Self:
        if (self.transit is None) == (self.event is None):
            raise ValueError("uma revelação tem de conter exatamente um trânsito ou evento")
        return self


class TransitCalculation(BaseModel):
    model_config = ConfigDict(frozen=True)

    library: str = "Swiss Ephemeris"
    library_version: str = SWISSEPH_VERSION
    orbs: dict[str, float]
    aspects: list[AspectKind]
    note: str = (
        "Orbes, pesos e escolha das revelações são convenções astrológicas; as posições e os "
        "momentos são cálculo astronómico."
    )


class DailySky(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    zone: str
    day_starts: AwareDatetime
    day_ends: AwareDatetime
    revelations: list[Revelation]
    tomorrow: Revelation | None
    active: list[Transit]
    upcoming: list[Transit]
    events: list[SkyEvent]
    calculation: TransitCalculation


def to_jd(instant: datetime) -> float:
    return _J2000 + (instant.astimezone(UTC) - _EPOCH).total_seconds() / 86400


def from_jd(jd: float) -> datetime:
    return (_EPOCH + timedelta(days=jd - _J2000)).replace(microsecond=0)


def _wrap(angle: float) -> float:
    """Ângulo em (−180, 180]."""
    value = angle % 360.0
    return value - 360.0 if value > 180 else value


def _bisect(f: Callable[[float], float], a: float, b: float, fa: float) -> float:
    while b - a > _MINUTE / 2:
        mid = (a + b) / 2
        fm = f(mid)
        if (fm < 0) == (fa < 0):
            a, fa = mid, fm
        else:
            b = mid
    return (a + b) / 2


def transit_orb(body: Body) -> float:
    return TRANSIT_ORBS.get(body, DEFAULT_SLOW_ORB)


class _Sky:
    """Amostras das posições num intervalo, com acesso pontual para refinar momentos."""

    def __init__(self, start: float, end: float, ephemeris_dir: Path | None) -> None:
        self.start, self.end, self.ephemeris_dir = start, end, ephemeris_dir
        self.samples: dict[Body, tuple[list[float], list[tuple[float, float]]]] = {}

    def at(self, body: Body, jd: float) -> tuple[float, float]:
        return ecliptic_positions([jd], body, ephemeris_dir=self.ephemeris_dir)[0]

    def sampled(
        self, body: Body, step: float, margin: float
    ) -> tuple[list[float], list[tuple[float, float]]]:
        if body not in self.samples:
            count = math.ceil((self.end - self.start + 2 * margin) / step) + 1
            jds = [self.start - margin + i * step for i in range(count)]
            self.samples[body] = (
                jds,
                ecliptic_positions(jds, body, ephemeris_dir=self.ephemeris_dir),
            )
        return self.samples[body]


def _natal_points(chart: NatalChart) -> dict[Body | Angle, float]:
    points: dict[Body | Angle, float] = {b.body: b.longitude for b in chart.bodies}
    points[Angle.ASCENDANT] = chart.angles.ascendant
    points[Angle.MIDHEAVEN] = chart.angles.midheaven
    return points


def _point_weight(point: Body | Angle) -> float:
    if point in (Body.SUN, Body.MOON, Angle.ASCENDANT, Angle.MIDHEAVEN):
        return 1.5
    if point in FAST:
        return 1.2
    return 1.0


def find_transits(
    chart: NatalChart, start: float, end: float, *, ephemeris_dir: Path | None = None
) -> list[Transit]:
    """Todos os períodos dentro da orbe que tocam [start, end] (dias julianos UT)."""
    sky = _Sky(start, end, ephemeris_dir)
    cusps = [h.longitude for h in chart.houses]
    found: list[Transit] = []
    for body in Body:
        orb = transit_orb(body)
        step = _STEP.get(body, 2.0)
        try:
            jds, positions = sky.sampled(body, step, _HORIZON.get(body, 400.0))
        except swe.Error:
            continue  # efeméride do corpo indisponível (ex.: Quíron sem ficheiro)
        lons = [p[0] for p in positions]
        for point, natal in _natal_points(chart).items():
            for kind in MAJOR_ASPECTS:
                targets = {(natal + kind.angle) % 360, (natal - kind.angle) % 360}
                for target in targets:
                    found.extend(
                        _periods(sky, body, point, kind, target, orb, jds, lons, start, end, cusps)
                    )
    return found


def _periods(
    sky: _Sky,
    body: Body,
    point: Body | Angle,
    kind: AspectKind,
    target: float,
    orb: float,
    jds: list[float],
    lons: list[float],
    start: float,
    end: float,
    cusps: list[float],
) -> list[Transit]:
    diffs = [_wrap(lon - target) for lon in lons]
    if min(abs(d) for d in diffs) > orb:
        return []

    def offset(jd: float) -> float:
        return _wrap(sky.at(body, jd)[0] - target)

    def outside(jd: float) -> float:
        return abs(offset(jd)) - orb

    result: list[Transit] = []
    i, n = 0, len(diffs)
    while i < n:
        if abs(diffs[i]) > orb:
            i += 1
            continue
        first = i
        while i + 1 < n and abs(diffs[i + 1]) <= orb:
            i += 1
        last = i
        i += 1
        starts = (
            _bisect(outside, jds[first - 1], jds[first], abs(diffs[first - 1]) - orb)
            if first > 0
            else None
        )
        ends = (
            _bisect(outside, jds[last], jds[last + 1], abs(diffs[last]) - orb)
            if last + 1 < n
            else None
        )
        if (starts is not None and starts > end) or (ends is not None and ends < start):
            continue
        lo, hi = max(first - 1, 0), min(last + 1, n - 1)
        exact = [
            from_jd(_bisect(offset, jds[k], jds[k + 1], diffs[k]))
            for k in range(lo, hi)
            if (diffs[k] < 0) != (diffs[k + 1] < 0) and abs(diffs[k] - diffs[k + 1]) < 90
        ]
        result.append(
            Transit(
                body=body,
                natal_point=point,
                kind=kind,
                allowed_orb=orb,
                starts=from_jd(starts) if starts is not None else None,
                ends=from_jd(ends) if ends is not None else None,
                exact=exact,
                natal_house=house_of(lons[last], cusps),
            )
        )
    return result


def _crossings(
    sky: _Sky,
    body: Body,
    boundaries: list[float],
    step: float,
) -> list[tuple[float, float]]:
    """Momentos em que o corpo atravessa cada longitude dada, no intervalo [start, end]."""
    jds, positions = sky.sampled(body, step, _HORIZON.get(body, 400.0))
    out: list[tuple[float, float]] = []
    for boundary in boundaries:

        def f(jd: float, boundary: float = boundary) -> float:
            return _wrap(sky.at(body, jd)[0] - boundary)

        for k in range(len(jds) - 1):
            if jds[k + 1] < sky.start or jds[k] > sky.end:
                continue
            a, b = _wrap(positions[k][0] - boundary), _wrap(positions[k + 1][0] - boundary)
            if (a < 0) != (b < 0) and abs(a - b) < 90:
                jd = _bisect(f, jds[k], jds[k + 1], a)
                if sky.start <= jd <= sky.end:
                    out.append((jd, boundary))
    return out


def find_events(
    chart: NatalChart, start: float, end: float, *, ephemeris_dir: Path | None = None
) -> list[SkyEvent]:
    sky = _Sky(start, end, ephemeris_dir)
    cusps = [h.longitude for h in chart.houses]
    points = _natal_points(chart)
    events: list[SkyEvent] = []
    for body in Body:
        if body is Body.MOON:
            continue
        step = _STEP.get(body, 2.0)
        weight = BODY_WEIGHT[body]
        try:
            sky.at(body, sky.start)
        except swe.Error:
            continue  # efeméride do corpo indisponível (ex.: Quíron sem ficheiro)
        for jd, _ in _crossings(sky, body, [30.0 * k for k in range(12)], step):
            lon, _ = sky.at(body, jd + _MINUTE)
            events.append(
                SkyEvent(
                    kind=EventKind.SIGN_INGRESS,
                    at=from_jd(jd),
                    body=body,
                    sign=Sign.of(lon),
                    weight=weight * 0.8,
                )
            )
        for jd, _boundary in _crossings(sky, body, cusps, step):
            lon, _ = sky.at(body, jd + _MINUTE)
            events.append(
                SkyEvent(
                    kind=EventKind.HOUSE_INGRESS,
                    at=from_jd(jd),
                    body=body,
                    sign=Sign.of(lon),
                    natal_house=house_of(lon, cusps),
                    weight=weight * 0.9,
                )
            )
        if body in (Body.SUN, Body.NORTH_NODE):
            continue
        jds, positions = sky.sampled(body, step, _HORIZON.get(body, 400.0))

        def speed(jd: float, body: Body = body) -> float:
            return sky.at(body, jd)[1]

        for k in range(len(jds) - 1):
            a, b = positions[k][1], positions[k + 1][1]
            if (a < 0) == (b < 0) or jds[k + 1] < start or jds[k] > end:
                continue
            jd = _bisect(speed, jds[k], jds[k + 1], a)
            if start <= jd <= end:
                lon, _ = sky.at(body, jd)
                events.append(
                    SkyEvent(
                        kind=EventKind.STATION_RETROGRADE if a > 0 else EventKind.STATION_DIRECT,
                        at=from_jd(jd),
                        body=body,
                        sign=Sign.of(lon),
                        natal_house=house_of(lon, cusps),
                        contacts=_contacts(lon, points, conjunction_only=True, orb=1.0),
                        weight=3.0 + weight * 0.3,
                    )
                )
    try:
        events.extend(_lunations(sky, cusps, points))
        events.extend(_eclipses(start, end, cusps, points, sky))
    except swe.Error:
        pass  # sem efeméride de Sol/Lua não há lunações nem eclipses calculáveis
    return sorted(events, key=lambda e: e.at)


def _contacts(
    lon: float,
    points: dict[Body | Angle, float],
    *,
    conjunction_only: bool = False,
    orb: float = LUNATION_CONTACT_ORB,
) -> list[Body | Angle]:
    hits = []
    for point, natal in points.items():
        separation = abs(_wrap(lon - natal))
        if separation <= orb or (not conjunction_only and 180 - separation <= orb):
            hits.append(point)
    return hits


def _lunations(sky: _Sky, cusps: list[float], points: dict[Body | Angle, float]) -> list[SkyEvent]:
    step = 0.25
    pad = step  # a amostragem pode ultrapassar o fim; só contam cruzamentos dentro do intervalo
    count = math.ceil((sky.end - sky.start + 2 * pad) / step) + 1
    jds = [sky.start - pad + i * step for i in range(count)]
    suns = ecliptic_positions(jds, Body.SUN, ephemeris_dir=sky.ephemeris_dir)
    moons = ecliptic_positions(jds, Body.MOON, ephemeris_dir=sky.ephemeris_dir)
    out: list[SkyEvent] = []
    for kind, phase in ((EventKind.NEW_MOON, 0.0), (EventKind.FULL_MOON, 180.0)):

        def elongation(jd: float, phase: float = phase) -> float:
            return _wrap(sky.at(Body.MOON, jd)[0] - sky.at(Body.SUN, jd)[0] - phase)

        values = [_wrap(m[0] - s[0] - phase) for s, m in zip(suns, moons, strict=True)]
        for k in range(len(jds) - 1):
            if (values[k] < 0) != (values[k + 1] < 0) and abs(values[k] - values[k + 1]) < 90:
                jd = _bisect(elongation, jds[k], jds[k + 1], values[k])
                if not sky.start <= jd <= sky.end:
                    continue
                lon, _ = sky.at(Body.MOON, jd)
                contacts = _contacts(lon, points)
                out.append(
                    SkyEvent(
                        kind=kind,
                        at=from_jd(jd),
                        body=Body.MOON,
                        sign=Sign.of(lon),
                        natal_house=house_of(lon, cusps),
                        contacts=contacts,
                        weight=2.5 + (1.5 if contacts else 0.0),
                    )
                )
    return out


_SOLAR_TYPES = (
    (swe.ECL_ANNULAR_TOTAL, "hybrid"),
    (swe.ECL_TOTAL, "total"),
    (swe.ECL_ANNULAR, "annular"),
    (swe.ECL_PARTIAL, "partial"),
)
_LUNAR_TYPES = (
    (swe.ECL_TOTAL, "total"),
    (swe.ECL_PARTIAL, "partial"),
    (swe.ECL_PENUMBRAL, "penumbral"),
)


def _eclipses(
    start: float,
    end: float,
    cusps: list[float],
    points: dict[Body | Angle, float],
    sky: _Sky,
) -> list[SkyEvent]:
    out: list[SkyEvent] = []
    searches = (
        (EventKind.SOLAR_ECLIPSE, swe.sol_eclipse_when_glob, _SOLAR_TYPES),
        (EventKind.LUNAR_ECLIPSE, swe.lun_eclipse_when, _LUNAR_TYPES),
    )
    for kind, search, types in searches:
        jd = start
        while True:
            flags, times = search(jd, swe.FLG_SWIEPH, 0, False)
            maximum = float(times[0])
            if maximum > end:
                break
            jd = maximum + 1
            lon, _ = sky.at(Body.MOON, maximum)
            contacts = _contacts(lon, points)
            out.append(
                SkyEvent(
                    kind=kind,
                    at=from_jd(maximum),
                    body=Body.SUN if kind is EventKind.SOLAR_ECLIPSE else Body.MOON,
                    sign=Sign.of(lon),
                    natal_house=house_of(lon, cusps),
                    eclipse_type=next((name for bit, name in types if flags & bit), None),
                    contacts=contacts,
                    weight=4.5 + (1.5 if contacts else 0.0),
                )
            )
    return out


def _exact_roots(
    jds: list[float], differences: list[float], offset: Callable[[float], float]
) -> list[float]:
    roots: list[float] = []
    for index, (left, right) in enumerate(pairwise(differences)):
        if abs(left) >= 10 or abs(right) >= 10 or abs(left - right) >= 90:
            continue
        if abs(left) < 1e-9:
            jd = jds[index]
        elif abs(right) < 1e-9:
            jd = jds[index + 1]
        elif (left < 0) != (right < 0):
            jd = _bisect(offset, jds[index], jds[index + 1], left)
        else:
            continue
        if not roots or abs(jd - roots[-1]) > _MINUTE:
            roots.append(jd)
    return roots


def _moon_sign_ingresses(sky: _Sky, cusps: list[float]) -> list[SkyEvent]:
    events = []
    boundaries = [30.0 * index for index in range(12)]
    for jd, _ in _crossings(sky, Body.MOON, boundaries, _STEP[Body.MOON]):
        if not sky.start <= jd < sky.end:
            continue
        longitude, _ = sky.at(Body.MOON, jd + _MINUTE)
        events.append(
            SkyEvent(
                kind=EventKind.MOON_SIGN_INGRESS,
                at=from_jd(jd),
                body=Body.MOON,
                sign=Sign.of(longitude),
                natal_house=house_of(longitude, cusps),
                weight=1.8,
            )
        )
    return events


def _sky_aspects(sky: _Sky, points: dict[Body | Angle, float]) -> list[SkyEvent]:
    planets = tuple(body for body in Body if body not in {Body.MOON, Body.NORTH_NODE, Body.CHIRON})
    step = _STEP[Body.SUN]
    samples: dict[Body, tuple[list[float], list[tuple[float, float]]]] = {}
    for body in planets:
        try:
            samples[body] = sky.sampled(body, step, 0.0)
        except swe.Error:
            continue

    events = []
    for body, other_body in combinations(planets, 2):
        if body not in samples or other_body not in samples:
            continue
        jds, body_positions = samples[body]
        other_positions = samples[other_body][1]
        for aspect in MAJOR_ASPECTS:
            targets = (
                (aspect.angle,)
                if aspect in (AspectKind.CONJUNCTION, AspectKind.OPPOSITION)
                else (aspect.angle, -aspect.angle)
            )
            for target in targets:
                differences = [
                    _wrap(position[0] - other[0] - target)
                    for position, other in zip(body_positions, other_positions, strict=True)
                ]

                def offset(
                    jd: float,
                    body: Body = body,
                    other_body: Body = other_body,
                    target: float = target,
                ) -> float:
                    return _wrap(sky.at(body, jd)[0] - sky.at(other_body, jd)[0] - target)

                for jd in _exact_roots(jds, differences, offset):
                    if not sky.start <= jd < sky.end:
                        continue
                    longitude, _ = sky.at(body, jd)
                    other_longitude, _ = sky.at(other_body, jd)
                    contacts = [
                        point
                        for point, natal_longitude in points.items()
                        if abs(_wrap(longitude - natal_longitude)) <= 1.0
                        or abs(_wrap(other_longitude - natal_longitude)) <= 1.0
                    ]
                    weight = (BODY_WEIGHT[body] + BODY_WEIGHT[other_body]) / 2 * ASPECT_WEIGHT[
                        aspect
                    ] * 0.5 + (1.0 if contacts else 0.0)
                    events.append(
                        SkyEvent(
                            kind=EventKind.SKY_ASPECT,
                            at=from_jd(jd),
                            body=body,
                            other_body=other_body,
                            aspect=aspect,
                            sign=Sign.of(longitude),
                            contacts=contacts,
                            weight=weight,
                        )
                    )
    return events


def _specificity_multiplier(transit: Transit, lo: datetime, hi: datetime) -> float:
    if any(lo <= instant < hi for instant in transit.exact):
        return 1.5
    if any(
        instant is not None and lo <= instant < hi for instant in (transit.starts, transit.ends)
    ):
        return 1.2
    if transit.body not in FAST and transit.body is not Body.MOON:
        return 0.55
    return 1.0


def _group_factors(factors: list[Factor]) -> list[Revelation]:
    groups: dict[tuple[str, Body | Angle | int], list[Factor]] = {}
    for index, factor in enumerate(factors):
        if factor.transit is not None:
            focus = factor.transit.natal_point
        elif factor.event is not None and factor.event.contacts:
            focus = factor.event.contacts[0]
        else:
            focus = None
        key = ("focus", focus) if focus is not None else ("single", index)
        groups.setdefault(key, []).append(factor)

    conclusions = []
    for (_, group_focus), group in groups.items():
        ranked = sorted(group, key=lambda factor: -factor.weight)
        principal, supporting = ranked[0], ranked[1:]
        focus = group_focus if isinstance(group_focus, (Body, Angle)) else None
        conclusions.append(
            Revelation(
                weight=round(principal.weight + 0.5 * sum(item.weight for item in supporting), 4),
                transit=principal.transit,
                event=principal.event,
                focus=focus,
                supporting=supporting[:3],
            )
        )
    return sorted(conclusions, key=lambda revelation: -revelation.weight)


def daily_sky(
    chart: NatalChart,
    day: date,
    zone: str,
    *,
    ephemeris_dir: Path | None = None,
) -> DailySky:
    if chart.settings.zodiac is not Zodiac.TROPICAL or chart.settings.node is not NodeType.TRUE:
        raise ValueError(
            "os trânsitos só estão calibrados para o zodíaco tropical e o Nodo verdadeiro"
        )
    tz = ZoneInfo(zone)
    day_starts = datetime.combine(day, time(), tz)
    day_ends = datetime.combine(day + timedelta(days=1), time(), tz)
    tomorrow_ends = datetime.combine(day + timedelta(days=2), time(), tz)
    start, end = to_jd(day_starts), to_jd(day_ends)
    horizon = to_jd(day_ends + timedelta(days=UPCOMING_DAYS))
    points = _natal_points(chart)
    cusps = [house.longitude for house in chart.houses]
    sky = _Sky(start, end, ephemeris_dir)
    middle = (start + end) / 2

    transits: list[Transit] = []
    for transit in find_transits(chart, start, horizon, ephemeris_dir=ephemeris_dir):
        lon, speed = sky.at(transit.body, middle)
        natal = points[transit.natal_point]
        deltas = [_wrap(lon - (natal + s * transit.kind.angle)) for s in (1, -1)]
        delta = min(deltas, key=abs)
        orb_now = abs(delta)
        weight = (
            BODY_WEIGHT[transit.body]
            * _point_weight(transit.natal_point)
            * ASPECT_WEIGHT[transit.kind]
            * (0.4 + 0.6 * max(0.0, 1 - orb_now / transit.allowed_orb))
        )
        transits.append(
            transit.model_copy(
                update={
                    "orb": round(orb_now, 4),
                    "applying": delta * speed < 0,
                    "weight": round(weight, 4),
                }
            )
        )

    def overlaps(t: Transit, lo: datetime, hi: datetime) -> bool:
        return (t.starts is None or t.starts < hi) and (t.ends is None or t.ends >= lo)

    def exact_between(t: Transit, lo: datetime, hi: datetime) -> bool:
        return any(lo <= x < hi for x in t.exact)

    active = sorted(
        (
            t
            for t in transits
            if overlaps(t, day_starts, day_ends)
            and (t.body is not Body.MOON or exact_between(t, day_starts, day_ends))
        ),
        key=lambda t: -t.weight,
    )
    upcoming = sorted(
        (
            t
            for t in transits
            if t.body is not Body.MOON and t.starts is not None and t.starts >= day_ends
        ),
        key=lambda t: t.starts or day_ends,
    )
    events = find_events(chart, start, horizon, ephemeris_dir=ephemeris_dir)
    special_sky = _Sky(start, to_jd(tomorrow_ends), ephemeris_dir)
    special_events = _moon_sign_ingresses(special_sky, cusps) + _sky_aspects(special_sky, points)

    def candidates(lo: datetime, hi: datetime, pool: list[Transit]) -> list[Revelation]:
        factors = [
            Factor(weight=t.weight * _specificity_multiplier(t, lo, hi), transit=t) for t in pool
        ]
        factors.extend(
            Factor(weight=event.weight, event=event)
            for event in (*events, *special_events)
            if lo <= event.at < hi
        )
        return _group_factors(factors)

    tomorrow_pool = [t for t in transits if exact_between(t, day_ends, tomorrow_ends)]
    tomorrow = candidates(day_ends, tomorrow_ends, tomorrow_pool)
    return DailySky(
        date=day,
        zone=zone,
        day_starts=day_starts,
        day_ends=day_ends,
        revelations=candidates(day_starts, day_ends, active)[:MAX_REVELATIONS],
        tomorrow=tomorrow[0] if tomorrow else None,
        active=active,
        upcoming=upcoming,
        events=events,
        calculation=TransitCalculation(
            orbs={body.value: transit_orb(body) for body in Body},
            aspects=list(MAJOR_ASPECTS),
        ),
    )
