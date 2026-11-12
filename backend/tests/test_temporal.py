from datetime import UTC, date, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from arquivo.temporal.intervals import Interval
from arquivo.temporal.local_time import ResolutionStatus, resolve_local_time
from arquivo.temporal.partial import PartialDate
from arquivo.temporal.precision import TemporalPrecision
from arquivo.temporal.stamps import Severity, TemporalStamp, check_chronology
from arquivo.temporal.zones import (
    TZDATA_VERSION,
    UnknownTimeZoneError,
    load_zone,
    zone_for_coordinates,
)


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


class TestLocalTime:
    def test_unique_summer_time_lisbon(self) -> None:
        result = resolve_local_time(datetime(2024, 7, 1, 12, 0), "Europe/Lisbon")
        assert result.status is ResolutionStatus.UNIQUE
        assert result.candidates[0].utc == utc(2024, 7, 1, 11, 0)
        assert result.candidates[0].abbreviation == "WEST"
        assert result.tzdata_version == TZDATA_VERSION

    def test_ambiguous_hour_at_end_of_dst(self) -> None:
        # 27/10/2024: em Lisboa, 01:30 acontece duas vezes (WEST e depois WET).
        result = resolve_local_time(datetime(2024, 10, 27, 1, 30), "Europe/Lisbon")
        assert result.status is ResolutionStatus.AMBIGUOUS
        assert [c.utc for c in result.candidates] == [
            utc(2024, 10, 27, 0, 30),
            utc(2024, 10, 27, 1, 30),
        ]
        assert result.earliest_utc == utc(2024, 10, 27, 0, 30)
        assert result.latest_utc == utc(2024, 10, 27, 1, 30)

    def test_nonexistent_hour_at_start_of_dst(self) -> None:
        # 31/03/2024: em Lisboa, os relógios saltam de 01:00 para 02:00.
        result = resolve_local_time(datetime(2024, 3, 31, 1, 30), "Europe/Lisbon")
        assert result.status is ResolutionStatus.NONEXISTENT
        assert len(result.candidates) == 2
        assert result.warnings

    def test_uncertainty_widens_the_interval(self) -> None:
        result = resolve_local_time(
            datetime(1990, 1, 15, 8, 0), "Europe/Lisbon", uncertainty_minutes=30
        )
        assert result.earliest_utc == utc(1990, 1, 15, 7, 30)
        assert result.latest_utc == utc(1990, 1, 15, 8, 30)

    def test_pre_1970_dates_are_flagged(self) -> None:
        result = resolve_local_time(datetime(1950, 6, 1, 12, 0), "Europe/Lisbon")
        assert any("1970" in w for w in result.warnings)

    def test_historical_offset_is_used_not_the_current_one(self) -> None:
        # Portugal usou CET (UTC+1) entre 1992 e 1996.
        result = resolve_local_time(datetime(1993, 1, 15, 12, 0), "Europe/Lisbon")
        assert result.candidates[0].utc_offset_seconds == 3600

    def test_local_mean_time_before_standard_time(self) -> None:
        # Antes de 1912, Lisboa usava a hora média local (-0:36:45).
        result = resolve_local_time(datetime(1900, 1, 1, 12, 0), "Europe/Lisbon")
        assert result.candidates[0].utc_offset_seconds == -(36 * 60 + 45)

    def test_rejects_aware_datetime(self) -> None:
        with pytest.raises(ValueError):
            resolve_local_time(datetime(2024, 1, 1, tzinfo=UTC), "Europe/Lisbon")

    @given(
        st.datetimes(min_value=datetime(1970, 1, 1), max_value=datetime(2037, 12, 31)),
        st.sampled_from(["Europe/Lisbon", "America/Sao_Paulo", "Atlantic/Azores", "Asia/Tokyo"]),
    )
    def test_valid_candidates_round_trip(self, local: datetime, zone: str) -> None:
        result = resolve_local_time(local, zone)
        assert result.earliest_utc <= result.latest_utc
        if result.status is not ResolutionStatus.NONEXISTENT:
            tz = load_zone(zone)
            for candidate in result.candidates:
                assert candidate.utc.astimezone(tz).replace(tzinfo=None) == local


class TestZones:
    def test_rejects_unknown_and_malicious_names(self) -> None:
        for name in ["Mars/Olympus", "../etc/passwd", "Europe/../../x"]:
            with pytest.raises(UnknownTimeZoneError):
                load_zone(name)

    def test_zone_from_coordinates(self) -> None:
        lookup = zone_for_coordinates(38.7223, -9.1393)
        assert lookup is not None
        assert lookup.zone == "Europe/Lisbon"
        assert lookup.warnings

    def test_azores_have_their_own_zone(self) -> None:
        lookup = zone_for_coordinates(37.7412, -25.6756)
        assert lookup is not None and lookup.zone == "Atlantic/Azores"


class TestPartialDate:
    def test_year_only(self) -> None:
        value = PartialDate.parse("1993")
        assert value.precision is TemporalPrecision.YEAR
        assert value.bounds() == (date(1993, 1, 1), date(1994, 1, 1))

    def test_month_bounds_handle_leap_years(self) -> None:
        assert PartialDate.parse("2024-02").bounds() == (date(2024, 2, 1), date(2024, 3, 1))
        assert PartialDate(year=2024, month=2).bounds()[1] - date(2024, 2, 1) == timedelta(29)

    def test_day_requires_month_and_valid_date(self) -> None:
        with pytest.raises(ValueError):
            PartialDate(year=2023, day=5)
        with pytest.raises(ValueError):
            PartialDate(year=2023, month=2, day=29)

    def test_approximate_is_shown(self) -> None:
        assert str(PartialDate.parse("1993-05", approximate=True)) == "c. 1993-05"

    def test_only_gregorian_supported_until_decided(self) -> None:
        with pytest.raises(ValueError):
            PartialDate(year=1500, calendar="julian")


class TestInterval:
    def test_half_open(self) -> None:
        interval = Interval(start=utc(2024, 1, 1), end=utc(2024, 2, 1))
        assert interval.contains(utc(2024, 1, 1))
        assert not interval.contains(utc(2024, 2, 1))

    def test_open_ended_and_overlap(self) -> None:
        a = Interval(start=utc(2024, 1, 1))
        b = Interval(end=utc(2024, 1, 2))
        assert a.overlaps(b)
        assert not Interval(end=utc(2024, 1, 1)).overlaps(a)

    def test_rejects_inverted_or_naive(self) -> None:
        with pytest.raises(ValueError):
            Interval(start=utc(2024, 2, 1), end=utc(2024, 1, 1))
        with pytest.raises(ValueError):
            Interval(start=datetime(2024, 1, 1))


class TestChronology:
    NOW = utc(2026, 1, 1)

    def codes(self, stamp: TemporalStamp) -> set[str]:
        return {issue.code for issue in check_chronology(stamp, now=self.NOW)}

    def test_consistent_stamp_has_no_issues(self) -> None:
        stamp = TemporalStamp(
            event_time=utc(2025, 1, 1),
            event_precision=TemporalPrecision.DAY,
            observed_at=utc(2025, 1, 2),
            recorded_at=utc(2025, 1, 3),
        )
        assert check_chronology(stamp, now=self.NOW) == []

    def test_detects_impossible_orderings(self) -> None:
        stamp = TemporalStamp(
            observed_at=utc(2025, 6, 1),
            recorded_at=utc(2025, 1, 1),
            executed_at=utc(2027, 1, 1),
        )
        assert {"recorded_before_observed", "executed_in_future"} <= self.codes(stamp)

    def test_observation_before_event_is_a_warning(self) -> None:
        stamp = TemporalStamp(
            event_time=utc(2025, 2, 1),
            event_precision=TemporalPrecision.DAY,
            observed_at=utc(2025, 1, 1),
            recorded_at=utc(2025, 1, 1),
        )
        issues = check_chronology(stamp, now=self.NOW)
        assert [(i.code, i.severity) for i in issues] == [
            ("observed_before_event", Severity.WARNING)
        ]

    def test_retrospective_forecast_flags_leakage_risk(self) -> None:
        stamp = TemporalStamp(
            recorded_at=utc(2025, 3, 1),
            forecast_window=Interval(start=utc(2025, 1, 1), end=utc(2025, 2, 1)),
        )
        assert "retrospective_forecast" in self.codes(stamp)
