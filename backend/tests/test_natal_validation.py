"""Validação cruzada: Swiss Ephemeris (cálculo) contra Skyfield + JPL DE421 (referência)."""

import math
from datetime import UTC, datetime

import numpy as np
import pytest

from arquivo.natal.chart import calculate_chart
from arquivo.natal.ephemeris import default_ephemeris_dir
from arquivo.natal.settings import Body, ChartSettings

DE421 = default_ephemeris_dir() / "de421.bsp"
pytestmark = pytest.mark.skipif(not DE421.is_file(), reason="DE421 em falta (fetch_ephemerides.sh)")

INSTANTS = [
    datetime(1900, 3, 15, 6, 0, tzinfo=UTC),
    datetime(1955, 7, 1, 0, 0, tzinfo=UTC),
    datetime(1993, 5, 20, 12, 35, tzinfo=UTC),
    datetime(2024, 10, 27, 0, 30, tzinfo=UTC),
]
PLACES = {
    "Lisboa": (38.7223, -9.1393),
    "Ponta Delgada": (37.7412, -25.6756),
    "São Paulo": (-23.5505, -46.6333),
    "Oslo": (59.9139, 10.7522),
}
TARGETS = {
    Body.SUN: "sun",
    Body.MOON: "moon",
    Body.MERCURY: "mercury",
    Body.VENUS: "venus",
    Body.MARS: "mars",
    Body.JUPITER: "jupiter barycenter",
    Body.SATURN: "saturn barycenter",
    Body.URANUS: "uranus barycenter",
    Body.NEPTUNE: "neptune barycenter",
    Body.PLUTO: "pluto barycenter",
}
ARCSEC = 1 / 3600


@pytest.fixture(scope="module")
def sky():  # type: ignore[no-untyped-def]
    from skyfield.api import load, load_file

    return load.timescale(), load_file(str(DE421))


def _time(ts, instant: datetime):  # type: ignore[no-untyped-def]
    # Antes de 1972 a hora civil é tempo solar médio (UT1); depois, UTC com segundos intercalares.
    if instant.year < 1972:
        return ts.ut1(instant.year, instant.month, instant.day, instant.hour, instant.minute)
    return ts.from_datetime(instant)


def _diff(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


@pytest.mark.parametrize("instant", INSTANTS, ids=lambda d: d.date().isoformat())
def test_planet_longitudes_agree_with_jpl(sky, instant: datetime) -> None:  # type: ignore[no-untyped-def]
    from skyfield.framelib import ecliptic_frame

    ts, eph = sky
    t = _time(ts, instant)
    earth = eph["earth"]
    chart = calculate_chart(instant, 38.7223, -9.1393, ChartSettings(bodies=tuple(TARGETS)))
    for position in chart.bodies:
        apparent = earth.at(t).observe(eph[TARGETS[position.body]]).apparent()
        _, lon, _ = apparent.frame_latlon(ecliptic_frame)
        tolerance = 5 * ARCSEC if position.body is Body.MOON else 2 * ARCSEC
        assert _diff(position.longitude, lon.degrees) < tolerance, position.body


@pytest.mark.parametrize("place", PLACES, ids=str)
@pytest.mark.parametrize("instant", INSTANTS, ids=lambda d: d.date().isoformat())
def test_angles_agree_with_sidereal_time(sky, instant: datetime, place: str) -> None:  # type: ignore[no-untyped-def]
    from skyfield.framelib import ecliptic_frame, true_equator_and_equinox_of_date

    ts, _ = sky
    lat, lon = PLACES[place]
    t = _time(ts, instant)
    pole = true_equator_and_equinox_of_date.rotation_at(t) @ ecliptic_frame.rotation_at(t).T
    eps = math.acos(float((pole @ np.array([0.0, 0.0, 1.0]))[2]))
    ramc = math.radians((t.gast * 15 + lon) % 360)
    mc = math.degrees(math.atan2(math.sin(ramc), math.cos(ramc) * math.cos(eps))) % 360
    asc = (
        math.degrees(
            math.atan2(
                math.cos(ramc),
                -(math.sin(ramc) * math.cos(eps) + math.tan(math.radians(lat)) * math.sin(eps)),
            )
        )
        % 360
    )
    chart = calculate_chart(instant, lat, lon, ChartSettings(bodies=(Body.SUN,)))
    assert _diff(chart.angles.midheaven, mc) < 5 * ARCSEC
    assert _diff(chart.angles.ascendant, asc) < 5 * ARCSEC
    assert _diff(chart.calculation.true_obliquity, math.degrees(eps)) < 1 * ARCSEC
