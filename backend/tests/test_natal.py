from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from arquivo.main import create_app
from arquivo.natal.chart import ChartError, calculate_chart, house_of
from arquivo.natal.ephemeris import EphemerisBackend, available_files, default_ephemeris_dir
from arquivo.natal.settings import (
    AspectKind,
    Ayanamsa,
    Body,
    ChartSettings,
    HouseSystem,
    Sign,
    Zodiac,
)

LISBON = (38.7223, -9.1393)
INSTANT = datetime(1993, 5, 20, 12, 35, tzinfo=UTC)
HAS_FILES = len(available_files(default_ephemeris_dir())) == 3
client = TestClient(create_app())


def test_defaults_follow_portuguese_practice() -> None:
    settings = ChartSettings()
    assert settings.zodiac is Zodiac.TROPICAL
    assert settings.house_system is HouseSystem.PLACIDUS
    assert set(settings.aspects) == {
        AspectKind.CONJUNCTION,
        AspectKind.SEXTILE,
        AspectKind.SQUARE,
        AspectKind.TRINE,
        AspectKind.OPPOSITION,
    }


def test_placidus_chart_is_consistent() -> None:
    chart = calculate_chart(INSTANT, *LISBON)
    assert [b.body for b in chart.bodies] == list(Body)
    assert chart.houses[0].longitude == pytest.approx(chart.angles.ascendant)
    assert chart.houses[9].longitude == pytest.approx(chart.angles.midheaven)
    cusps = [h.longitude for h in chart.houses]
    for body in chart.bodies:
        assert body.sign is Sign.of(body.longitude)
        assert 0 <= body.degree_in_sign < 30
        assert body.house == house_of(body.longitude, cusps)
    assert not chart.calculation.warnings
    if HAS_FILES:
        assert chart.calculation.backend is EphemerisBackend.SWISS_FILES


def test_sun_position_on_reference_date() -> None:
    chart = calculate_chart(INSTANT, *LISBON)
    sun = next(b for b in chart.bodies if b.body is Body.SUN)
    assert sun.sign is Sign.TAURUS
    assert sun.degree_in_sign == pytest.approx(29.50, abs=0.01)


def test_equal_and_whole_sign_houses() -> None:
    equal = calculate_chart(INSTANT, *LISBON, ChartSettings(house_system=HouseSystem.EQUAL))
    asc = equal.angles.ascendant
    for i, cusp in enumerate(equal.houses):
        assert cusp.longitude == pytest.approx((asc + 30 * i) % 360)
    whole = calculate_chart(INSTANT, *LISBON, ChartSettings(house_system=HouseSystem.WHOLE_SIGN))
    assert whole.houses[0].longitude == pytest.approx(asc // 30 * 30)
    assert all(c.degree_in_sign == pytest.approx(0) for c in whole.houses)


def test_placidus_is_refused_above_polar_circle() -> None:
    with pytest.raises(ChartError, match="círculo polar"):
        calculate_chart(INSTANT, 70.0, 25.0)
    chart = calculate_chart(INSTANT, 70.0, 25.0, ChartSettings(house_system=HouseSystem.PORPHYRY))
    assert len(chart.houses) == 12


def test_sidereal_requires_ayanamsa_and_shifts_longitudes() -> None:
    with pytest.raises(ValueError, match="ayanamsa"):
        ChartSettings(zodiac=Zodiac.SIDEREAL)
    tropical = calculate_chart(INSTANT, *LISBON)
    sidereal = calculate_chart(
        INSTANT, *LISBON, ChartSettings(zodiac=Zodiac.SIDEREAL, ayanamsa=Ayanamsa.LAHIRI)
    )
    ayanamsa = sidereal.calculation.ayanamsa
    assert ayanamsa == pytest.approx(23.78, abs=0.05)
    sun_t = tropical.bodies[0].longitude
    sun_s = sidereal.bodies[0].longitude
    assert (sun_t - sun_s) % 360 == pytest.approx(ayanamsa, abs=1e-4)


def test_aspects_respect_orbs() -> None:
    settings = ChartSettings()
    chart = calculate_chart(INSTANT, *LISBON, settings)
    assert chart.aspects
    for aspect in chart.aspects:
        bonus = 2 if {aspect.first, aspect.second} & {Body.SUN, Body.MOON} else 0
        assert aspect.orb <= settings.orbs[aspect.kind] + bonus
        assert aspect.orb == pytest.approx(abs(aspect.separation - aspect.kind.angle))
    tight = ChartSettings(orbs={k: 0.1 for k in AspectKind})
    assert len(calculate_chart(INSTANT, *LISBON, tight).aspects) < len(chart.aspects)


def test_missing_files_fall_back_to_moshier_with_warning(tmp_path: Path) -> None:
    settings = ChartSettings(bodies=(Body.SUN, Body.MOON))
    chart = calculate_chart(INSTANT, *LISBON, settings, ephemeris_dir=tmp_path)
    assert chart.calculation.backend is EphemerisBackend.MOSHIER
    assert any("Moshier" in w for w in chart.calculation.warnings)


def test_rejects_naive_instant() -> None:
    with pytest.raises(ValueError):
        calculate_chart(datetime(1993, 5, 20, 12, 35), *LISBON)


def test_api_chart_from_birth_data() -> None:
    response = client.post(
        "/api/v1/natal/chart",
        json={
            "birth_date": "1993-05-20",
            "birth_time": "14:35",
            "latitude": LISBON[0],
            "longitude": LISBON[1],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["birth"]["zone"] == "Europe/Lisbon"
    assert body["birth"]["utc"] == "1993-05-20T12:35:00Z"
    assert body["chart"]["settings"]["house_system"] == "placidus"
    assert len(body["chart"]["houses"]) == 12


def test_api_rejects_inexact_birth_time() -> None:
    response = client.post(
        "/api/v1/natal/chart",
        json={
            "birth_date": "2024-10-27",
            "birth_time": "01:30",
            "latitude": LISBON[0],
            "longitude": LISBON[1],
        },
    )
    assert response.status_code == 422
    assert "duas vezes" in response.json()["detail"]


def test_api_options_are_labelled_in_portuguese() -> None:
    body = client.get("/api/v1/natal/options").json()
    labels = {o["id"]: o["label"] for o in body["house_systems"]}
    assert labels["placidus"] == "Placidus"
    assert {o["id"]: o["label"] for o in body["signs"]}["aries"] == "Carneiro"
    assert body["defaults"]["zodiac"] == "tropical"
