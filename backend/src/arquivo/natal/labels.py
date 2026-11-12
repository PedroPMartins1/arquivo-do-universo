"""Nomes apresentados ao utilizador. Organizado por locale para facilitar a expansão."""

from enum import StrEnum

from arquivo.natal.settings import AspectKind, Ayanamsa, Body, HouseSystem, Sign, Zodiac

DEFAULT_LOCALE = "pt-PT"

_PT: dict[StrEnum, str] = {
    Sign.ARIES: "Carneiro",
    Sign.TAURUS: "Touro",
    Sign.GEMINI: "Gémeos",
    Sign.CANCER: "Caranguejo",
    Sign.LEO: "Leão",
    Sign.VIRGO: "Virgem",
    Sign.LIBRA: "Balança",
    Sign.SCORPIO: "Escorpião",
    Sign.SAGITTARIUS: "Sagitário",
    Sign.CAPRICORN: "Capricórnio",
    Sign.AQUARIUS: "Aquário",
    Sign.PISCES: "Peixes",
    Body.SUN: "Sol",
    Body.MOON: "Lua",
    Body.MERCURY: "Mercúrio",
    Body.VENUS: "Vénus",
    Body.MARS: "Marte",
    Body.JUPITER: "Júpiter",
    Body.SATURN: "Saturno",
    Body.URANUS: "Úrano",
    Body.NEPTUNE: "Neptuno",
    Body.PLUTO: "Plutão",
    Body.NORTH_NODE: "Nodo Norte",
    Body.CHIRON: "Quíron",
    AspectKind.CONJUNCTION: "Conjunção",
    AspectKind.SEXTILE: "Sextil",
    AspectKind.SQUARE: "Quadratura",
    AspectKind.TRINE: "Trígono",
    AspectKind.OPPOSITION: "Oposição",
    AspectKind.SEMISEXTILE: "Semi-sextil",
    AspectKind.SEMISQUARE: "Semiquadratura",
    AspectKind.SESQUIQUADRATE: "Sesquiquadratura",
    AspectKind.QUINCUNX: "Quincôncio",
    HouseSystem.PLACIDUS: "Placidus",
    HouseSystem.KOCH: "Koch",
    HouseSystem.PORPHYRY: "Porfírio",
    HouseSystem.REGIOMONTANUS: "Regiomontanus",
    HouseSystem.CAMPANUS: "Campanus",
    HouseSystem.EQUAL: "Casas iguais",
    HouseSystem.WHOLE_SIGN: "Signos inteiros",
    HouseSystem.ALCABITIUS: "Alcabitius",
    HouseSystem.TOPOCENTRIC: "Topocêntrico",
    HouseSystem.MORINUS: "Morinus",
    HouseSystem.MERIDIAN: "Meridiano",
    Zodiac.TROPICAL: "Tropical",
    Zodiac.SIDEREAL: "Sideral",
    Ayanamsa.LAHIRI: "Lahiri",
    Ayanamsa.FAGAN_BRADLEY: "Fagan-Bradley",
    Ayanamsa.RAMAN: "Raman",
    Ayanamsa.KRISHNAMURTI: "Krishnamurti",
}

LABELS: dict[str, dict[StrEnum, str]] = {"pt-PT": _PT}


def label(value: StrEnum, locale: str = DEFAULT_LOCALE) -> str:
    return LABELS.get(locale, _PT).get(value, value.value)
