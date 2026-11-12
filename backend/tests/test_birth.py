from datetime import UTC, date, datetime, time

import pytest

from arquivo.natal.birth import InexactBirthDataError, resolve_birth_instant


def test_exact_birth_resolves_to_single_instant() -> None:
    instant = resolve_birth_instant(date(1993, 5, 20), time(14, 35), "Europe/Lisbon")
    # Em maio de 1993 Portugal estava em CEST (UTC+2).
    assert instant.utc == datetime(1993, 5, 20, 12, 35, tzinfo=UTC)
    assert instant.utc_offset_seconds == 7200


def test_ambiguous_hour_requires_explicit_occurrence() -> None:
    with pytest.raises(InexactBirthDataError, match="duas vezes"):
        resolve_birth_instant(date(2024, 10, 27), time(1, 30), "Europe/Lisbon")
    first = resolve_birth_instant(date(2024, 10, 27), time(1, 30), "Europe/Lisbon", occurrence=0)
    second = resolve_birth_instant(date(2024, 10, 27), time(1, 30), "Europe/Lisbon", occurrence=1)
    assert (second.utc - first.utc).total_seconds() == 3600


def test_nonexistent_hour_is_rejected() -> None:
    with pytest.raises(InexactBirthDataError, match="não existiu"):
        resolve_birth_instant(date(2024, 3, 31), time(1, 30), "Europe/Lisbon")


def test_time_is_recorded_to_the_minute() -> None:
    with pytest.raises(InexactBirthDataError):
        resolve_birth_instant(date(1993, 5, 20), time(14, 35, 10), "Europe/Lisbon")
