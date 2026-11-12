"""Acesso à Swiss Ephemeris (AGPL). Regista que efemérides foram efetivamente usadas."""

from enum import StrEnum
from pathlib import Path

import swisseph as swe

from arquivo.config import get_settings

SWISSEPH_VERSION: str = str(swe.version)
EPHEMERIS_FILES = ("sepl_18.se1", "semo_18.se1", "seas_18.se1")


class EphemerisBackend(StrEnum):
    SWISS_FILES = "swiss_ephemeris_files"
    MOSHIER = "moshier"


def default_ephemeris_dir() -> Path:
    return get_settings().ephemeris_path


def available_files(directory: Path) -> list[str]:
    return [name for name in EPHEMERIS_FILES if (directory / name).is_file()]
