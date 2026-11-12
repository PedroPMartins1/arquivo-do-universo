"""Configuração do Mapa Natal: zodíaco, sistema de casas, corpos, aspetos e orbes.

Os valores por omissão seguem a prática corrente em Portugal (D-021): zodíaco tropical, casas
Placidus, aspetos ptolemaicos. Tudo é configurável; orbes são convenção astrológica, não física.
"""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Zodiac(StrEnum):
    TROPICAL = "tropical"
    SIDEREAL = "sidereal"


class Ayanamsa(StrEnum):
    LAHIRI = "lahiri"
    FAGAN_BRADLEY = "fagan_bradley"
    RAMAN = "raman"
    KRISHNAMURTI = "krishnamurti"


class HouseSystem(StrEnum):
    PLACIDUS = "placidus"
    KOCH = "koch"
    PORPHYRY = "porphyry"
    REGIOMONTANUS = "regiomontanus"
    CAMPANUS = "campanus"
    EQUAL = "equal"
    WHOLE_SIGN = "whole_sign"
    ALCABITIUS = "alcabitius"
    TOPOCENTRIC = "topocentric"
    MORINUS = "morinus"
    MERIDIAN = "meridian"

    @property
    def swe_code(self) -> bytes:
        return _HOUSE_CODES[self]

    @property
    def undefined_in_polar_regions(self) -> bool:
        return self in {HouseSystem.PLACIDUS, HouseSystem.KOCH, HouseSystem.TOPOCENTRIC}


_HOUSE_CODES: dict[HouseSystem, bytes] = {
    HouseSystem.PLACIDUS: b"P",
    HouseSystem.KOCH: b"K",
    HouseSystem.PORPHYRY: b"O",
    HouseSystem.REGIOMONTANUS: b"R",
    HouseSystem.CAMPANUS: b"C",
    HouseSystem.EQUAL: b"A",
    HouseSystem.WHOLE_SIGN: b"W",
    HouseSystem.ALCABITIUS: b"B",
    HouseSystem.TOPOCENTRIC: b"T",
    HouseSystem.MORINUS: b"M",
    HouseSystem.MERIDIAN: b"X",
}


class Body(StrEnum):
    SUN = "sun"
    MOON = "moon"
    MERCURY = "mercury"
    VENUS = "venus"
    MARS = "mars"
    JUPITER = "jupiter"
    SATURN = "saturn"
    URANUS = "uranus"
    NEPTUNE = "neptune"
    PLUTO = "pluto"
    NORTH_NODE = "north_node"
    CHIRON = "chiron"


LUMINARIES = frozenset({Body.SUN, Body.MOON})


class NodeType(StrEnum):
    TRUE = "true"
    MEAN = "mean"


class Sign(StrEnum):
    ARIES = "aries"
    TAURUS = "taurus"
    GEMINI = "gemini"
    CANCER = "cancer"
    LEO = "leo"
    VIRGO = "virgo"
    LIBRA = "libra"
    SCORPIO = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN = "capricorn"
    AQUARIUS = "aquarius"
    PISCES = "pisces"

    @classmethod
    def of(cls, longitude: float) -> "Sign":
        return list(cls)[int(longitude % 360 // 30)]


class AspectKind(StrEnum):
    CONJUNCTION = "conjunction"
    SEXTILE = "sextile"
    SQUARE = "square"
    TRINE = "trine"
    OPPOSITION = "opposition"
    SEMISEXTILE = "semisextile"
    SEMISQUARE = "semisquare"
    SESQUIQUADRATE = "sesquiquadrate"
    QUINCUNX = "quincunx"

    @property
    def angle(self) -> float:
        return _ASPECT_ANGLES[self]


_ASPECT_ANGLES: dict[AspectKind, float] = {
    AspectKind.CONJUNCTION: 0,
    AspectKind.SEXTILE: 60,
    AspectKind.SQUARE: 90,
    AspectKind.TRINE: 120,
    AspectKind.OPPOSITION: 180,
    AspectKind.SEMISEXTILE: 30,
    AspectKind.SEMISQUARE: 45,
    AspectKind.SESQUIQUADRATE: 135,
    AspectKind.QUINCUNX: 150,
}

MAJOR_ASPECTS = (
    AspectKind.CONJUNCTION,
    AspectKind.SEXTILE,
    AspectKind.SQUARE,
    AspectKind.TRINE,
    AspectKind.OPPOSITION,
)

DEFAULT_ORBS: dict[AspectKind, float] = {
    AspectKind.CONJUNCTION: 8,
    AspectKind.OPPOSITION: 8,
    AspectKind.TRINE: 7,
    AspectKind.SQUARE: 7,
    AspectKind.SEXTILE: 5,
    AspectKind.QUINCUNX: 3,
    AspectKind.SEMISEXTILE: 2,
    AspectKind.SEMISQUARE: 2,
    AspectKind.SESQUIQUADRATE: 2,
}


class ChartSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    zodiac: Zodiac = Zodiac.TROPICAL
    ayanamsa: Ayanamsa | None = None
    house_system: HouseSystem = HouseSystem.PLACIDUS
    node: NodeType = NodeType.TRUE
    bodies: tuple[Body, ...] = tuple(Body)
    aspects: tuple[AspectKind, ...] = MAJOR_ASPECTS
    orbs: dict[AspectKind, float] = Field(default_factory=lambda: dict(DEFAULT_ORBS))
    luminary_orb_bonus: float = Field(default=2, ge=0, le=5)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.zodiac is Zodiac.SIDEREAL and self.ayanamsa is None:
            raise ValueError("o zodíaco sideral exige a escolha de um ayanamsa")
        if self.zodiac is Zodiac.TROPICAL and self.ayanamsa is not None:
            raise ValueError("o ayanamsa só se aplica ao zodíaco sideral")
        missing = [a.value for a in self.aspects if a not in self.orbs]
        if missing:
            raise ValueError(f"falta a orbe dos aspetos: {missing}")
        if any(not 0 <= orb <= 15 for orb in self.orbs.values()):
            raise ValueError("as orbes têm de estar entre 0° e 15°")
        if len(set(self.bodies)) != len(self.bodies):
            raise ValueError("corpos repetidos")
        return self
