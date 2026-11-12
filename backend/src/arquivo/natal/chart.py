"""Cálculo do Mapa Natal com a Swiss Ephemeris.

As posições são cálculos astronómicos (geocêntricas, aparentes, equinócio verdadeiro da data).
Casas, aspetos e orbes são convenções astrológicas e ficam registados com o resultado.
Antes de 1972 a hora civil é tratada como UT1 (tempo solar médio), como faz a Swiss Ephemeris.
O ayanamsa devolvido inclui a nutação, para coincidir com as longitudes siderais.
"""

import math
import threading
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path

import swisseph as swe
from pydantic import AwareDatetime, BaseModel, ConfigDict

from arquivo.natal.ephemeris import (
    SWISSEPH_VERSION,
    EphemerisBackend,
    available_files,
    default_ephemeris_dir,
)
from arquivo.natal.settings import (
    LUMINARIES,
    AspectKind,
    Ayanamsa,
    Body,
    ChartSettings,
    NodeType,
    Sign,
    Zodiac,
)

# A Swiss Ephemeris tem estado global (caminho, modo sideral): serializar as chamadas.
_LOCK = threading.Lock()

_BODY_IDS: dict[Body, int] = {
    Body.SUN: swe.SUN,
    Body.MOON: swe.MOON,
    Body.MERCURY: swe.MERCURY,
    Body.VENUS: swe.VENUS,
    Body.MARS: swe.MARS,
    Body.JUPITER: swe.JUPITER,
    Body.SATURN: swe.SATURN,
    Body.URANUS: swe.URANUS,
    Body.NEPTUNE: swe.NEPTUNE,
    Body.PLUTO: swe.PLUTO,
    Body.CHIRON: swe.CHIRON,
}
_NODE_IDS = {NodeType.TRUE: swe.TRUE_NODE, NodeType.MEAN: swe.MEAN_NODE}
_SIDEREAL_MODES = {
    Ayanamsa.LAHIRI: swe.SIDM_LAHIRI,
    Ayanamsa.FAGAN_BRADLEY: swe.SIDM_FAGAN_BRADLEY,
    Ayanamsa.RAMAN: swe.SIDM_RAMAN,
    Ayanamsa.KRISHNAMURTI: swe.SIDM_KRISHNAMURTI,
}


class ChartError(ValueError):
    """O mapa não pode ser calculado com a configuração pedida."""


class BodyPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    body: Body
    longitude: float
    latitude: float
    distance_au: float
    speed: float
    retrograde: bool
    sign: Sign
    degree_in_sign: float
    house: int


class HouseCusp(BaseModel):
    model_config = ConfigDict(frozen=True)

    house: int
    longitude: float
    sign: Sign
    degree_in_sign: float


class Angles(BaseModel):
    model_config = ConfigDict(frozen=True)

    ascendant: float
    midheaven: float
    descendant: float
    imum_coeli: float
    vertex: float
    armc: float


class Aspect(BaseModel):
    model_config = ConfigDict(frozen=True)

    first: Body
    second: Body
    kind: AspectKind
    separation: float
    orb: float
    allowed_orb: float
    applying: bool


class Calculation(BaseModel):
    model_config = ConfigDict(frozen=True)

    library: str = "Swiss Ephemeris"
    library_version: str
    backend: EphemerisBackend
    ephemeris_files: list[str]
    julian_day_ut: float
    julian_day_tt: float
    true_obliquity: float
    ayanamsa: float | None
    warnings: list[str]


class NatalChart(BaseModel):
    model_config = ConfigDict(frozen=True)

    instant_utc: AwareDatetime
    latitude: float
    longitude: float
    settings: ChartSettings
    bodies: list[BodyPosition]
    houses: list[HouseCusp]
    angles: Angles
    aspects: list[Aspect]
    calculation: Calculation


def _norm(angle: float) -> float:
    return angle % 360.0


def _separation(a: float, b: float) -> float:
    diff = abs(_norm(a) - _norm(b))
    return 360.0 - diff if diff > 180 else diff


def _signed_difference(a: float, b: float) -> float:
    """Diferença b − a no intervalo (−180, 180]."""
    diff = _norm(b - a)
    return diff - 360.0 if diff > 180 else diff


def _is_applying(a: BodyPosition, b: BodyPosition, angle: float) -> bool:
    """Aplicativo se a orbe está a diminuir no próprio instante (derivada, não projeção)."""
    diff = _signed_difference(a.longitude, b.longitude)
    separation_rate = math.copysign(1.0, diff) * (b.speed - a.speed) if diff else 0.0
    offset = abs(diff) - angle
    if offset == 0:
        return False
    return math.copysign(1.0, offset) * separation_rate < 0


def house_of(longitude: float, cusps: list[float]) -> int:
    for index, start in enumerate(cusps):
        end = cusps[(index + 1) % 12]
        if _norm(longitude - start) < _norm(end - start):
            return index + 1
    raise ChartError("cúspides de casas inválidas")  # pragma: no cover


def find_aspects(bodies: list[BodyPosition], settings: ChartSettings) -> list[Aspect]:
    found: list[Aspect] = []
    for a, b in combinations(bodies, 2):
        separation = _separation(a.longitude, b.longitude)
        bonus = settings.luminary_orb_bonus if {a.body, b.body} & LUMINARIES else 0.0
        best: Aspect | None = None
        for kind in settings.aspects:
            orb = abs(separation - kind.angle)
            allowed = settings.orbs[kind] + bonus
            if orb <= allowed and (best is None or orb < best.orb):
                best = Aspect(
                    first=a.body,
                    second=b.body,
                    kind=kind,
                    separation=separation,
                    orb=orb,
                    allowed_orb=allowed,
                    applying=_is_applying(a, b, kind.angle),
                )
        if best is not None:
            found.append(best)
    return sorted(found, key=lambda aspect: aspect.orb)


def calculate_chart(
    instant: datetime,
    latitude: float,
    longitude: float,
    settings: ChartSettings | None = None,
    *,
    ephemeris_dir: Path | None = None,
) -> NatalChart:
    if instant.tzinfo is None:
        raise ValueError("o instante tem de ter fuso (UTC)")
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("coordenadas fora do intervalo válido")
    settings = settings or ChartSettings()
    directory = ephemeris_dir or default_ephemeris_dir()
    utc = instant.astimezone(UTC)
    seconds = utc.second + utc.microsecond / 1e6

    with _LOCK:
        swe.set_ephe_path(str(directory))
        jd_tt, jd_ut = swe.utc_to_jd(
            utc.year, utc.month, utc.day, utc.hour, utc.minute, seconds, swe.GREG_CAL
        )
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        house_flags = 0
        ayanamsa: float | None = None
        if settings.zodiac is Zodiac.SIDEREAL:
            assert settings.ayanamsa is not None
            swe.set_sid_mode(_SIDEREAL_MODES[settings.ayanamsa], 0, 0)
            flags |= swe.FLG_SIDEREAL
            house_flags = swe.FLG_SIDEREAL
            ayanamsa = float(swe.get_ayanamsa_ex_ut(jd_ut, flags)[1])

        obliquity = float(swe.calc_ut(jd_ut, swe.ECL_NUT, 0)[0][0])
        if settings.house_system.undefined_in_polar_regions and abs(latitude) >= 90 - obliquity:
            raise ChartError(
                f"o sistema de casas '{settings.house_system.value}' não está definido acima do "
                "círculo polar; escolher, por exemplo, Porfírio, casas iguais ou signos inteiros"
            )

        warnings: list[str] = []
        moshier_bodies: list[Body] = []
        used_swiss_files = False
        raw: list[tuple[Body, tuple[float, ...]]] = []
        for body in settings.bodies:
            body_id = _NODE_IDS[settings.node] if body is Body.NORTH_NODE else _BODY_IDS[body]
            try:
                values, returned = swe.calc_ut(jd_ut, body_id, flags)
            except swe.Error as error:
                warnings.append(f"{body.value} não calculado: {error}")
                continue
            if returned & swe.FLG_SWIEPH:
                used_swiss_files = True
            else:
                moshier_bodies.append(body)
            raw.append((body, tuple(float(v) for v in values)))

        cusps_raw, ascmc = swe.houses_ex(
            jd_ut, latitude, longitude, settings.house_system.swe_code, house_flags
        )

    cusps = [_norm(float(c)) for c in cusps_raw[:12]]
    bodies = [
        BodyPosition(
            body=body,
            longitude=_norm(values[0]),
            latitude=values[1],
            distance_au=values[2],
            speed=values[3],
            retrograde=values[3] < 0,
            sign=Sign.of(values[0]),
            degree_in_sign=_norm(values[0]) % 30,
            house=house_of(values[0], cusps),
        )
        for body, values in raw
    ]
    houses = [
        HouseCusp(house=i + 1, longitude=c, sign=Sign.of(c), degree_in_sign=c % 30)
        for i, c in enumerate(cusps)
    ]
    asc, mc = _norm(float(ascmc[0])), _norm(float(ascmc[1]))
    angles = Angles(
        ascendant=asc,
        midheaven=mc,
        descendant=_norm(asc + 180),
        imum_coeli=_norm(mc + 180),
        vertex=_norm(float(ascmc[3])),
        armc=_norm(float(ascmc[2])),
    )

    files = available_files(directory) if used_swiss_files else []
    backend = EphemerisBackend.MOSHIER if moshier_bodies else EphemerisBackend.SWISS_FILES
    if moshier_bodies:
        names = ", ".join(body.value for body in moshier_bodies)
        warnings.append(
            "ficheiros da Swiss Ephemeris indisponíveis para esta data: usado o modelo de "
            f"Moshier (precisão inferior) para {names}"
        )
    if not math.isclose(cusps[0], asc, abs_tol=1e-6) and settings.house_system.value not in {
        "whole_sign",
        "meridian",
        "morinus",
    }:
        warnings.append("a cúspide da casa 1 não coincide com o Ascendente")

    return NatalChart(
        instant_utc=utc,
        latitude=latitude,
        longitude=longitude,
        settings=settings,
        bodies=bodies,
        houses=houses,
        angles=angles,
        aspects=find_aspects(bodies, settings),
        calculation=Calculation(
            library_version=SWISSEPH_VERSION,
            backend=backend,
            ephemeris_files=files,
            julian_day_ut=float(jd_ut),
            julian_day_tt=float(jd_tt),
            true_obliquity=obliquity,
            ayanamsa=ayanamsa,
            warnings=warnings,
        ),
    )
