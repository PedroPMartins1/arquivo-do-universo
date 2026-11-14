from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from arquivo.config import Settings
from arquivo.transits.unlock import unlock_times

SLOTS = [time(9), time(11), time(13), time(15), time(17)]
DAY = date(2026, 11, 16)
LISBON = ZoneInfo("Europe/Lisbon")


def test_default_revelation_unlock_times(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARQUIVO_REVELATION_UNLOCK_TIMES", raising=False)
    assert Settings(_env_file=None).revelation_unlock_times == SLOTS


def test_unlock_times_uses_all_five_slots() -> None:
    assert unlock_times(DAY, LISBON, 5, SLOTS) == [
        datetime(2026, 11, 16, hour, tzinfo=LISBON) for hour in (9, 11, 13, 15, 17)
    ]


def test_unlock_times_spreads_three_revelations_between_endpoints() -> None:
    assert unlock_times(DAY, LISBON, 3, SLOTS) == [
        datetime(2026, 11, 16, hour, tzinfo=LISBON) for hour in (9, 13, 17)
    ]


def test_unlock_times_handles_one_and_zero_revelations() -> None:
    assert unlock_times(DAY, LISBON, 1, SLOTS) == [datetime(2026, 11, 16, 9, tzinfo=LISBON)]
    assert unlock_times(DAY, LISBON, 0, SLOTS) == []


def test_unlock_times_rejects_more_revelations_than_slots() -> None:
    with pytest.raises(ValueError, match="horários de abertura suficientes"):
        unlock_times(DAY, LISBON, 6, SLOTS)


def test_unlock_times_uses_zoneinfo_fold_zero_for_nonexistent_local_time() -> None:
    nonexistent = time(1, 30)
    result = unlock_times(
        date(2026, 3, 29), LISBON, 5, [time(0), nonexistent, time(2), time(3), time(4)]
    )
    assert result[1].hour == 1
    assert result[1].minute == 30
    assert result[1].fold == 0
    assert result[1].utcoffset() == timedelta(0)


def test_unlock_times_keep_local_schedule_on_dst_transition_day() -> None:
    result = unlock_times(date(2026, 3, 29), LISBON, 5, SLOTS)
    assert [instant.hour for instant in result] == [9, 11, 13, 15, 17]
    assert all(instant.utcoffset() == timedelta(hours=1) for instant in result)


def test_revelation_unlock_times_must_be_nonempty_and_increasing() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, revelation_unlock_times=[])
    with pytest.raises(ValidationError, match="são precisos pelo menos 5 horários de abertura"):
        Settings(
            _env_file=None,
            revelation_unlock_times=[time(7), time(10), time(13), time(16)],
        )
    with pytest.raises(ValidationError):
        Settings(_env_file=None, revelation_unlock_times=[time(7), time(7)])
    with pytest.raises(ValidationError):
        Settings(_env_file=None, revelation_unlock_times=[time(10), time(7)])
