"""Modelo temporal comum: os vários tempos de uma informação, nunca confundidos (dossiê §18.1)."""

from datetime import datetime, timedelta
from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict

from arquivo.temporal.intervals import Interval
from arquivo.temporal.precision import TemporalPrecision

CLOCK_SKEW = timedelta(minutes=5)


class TemporalStamp(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_time: AwareDatetime | None = None
    event_precision: TemporalPrecision = TemporalPrecision.UNKNOWN
    observed_at: AwareDatetime | None = None
    recorded_at: AwareDatetime
    valid: Interval | None = None
    forecast_window: Interval | None = None
    executed_at: AwareDatetime | None = None
    sequence: int | None = None


class Severity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


class ChronologyIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    severity: Severity
    message: str


def check_chronology(stamp: TemporalStamp, *, now: datetime) -> list[ChronologyIssue]:
    issues: list[ChronologyIssue] = []

    def add(code: str, severity: Severity, message: str) -> None:
        issues.append(ChronologyIssue(code=code, severity=severity, message=message))

    if stamp.event_time is None and stamp.event_precision is not TemporalPrecision.UNKNOWN:
        add(
            "precision_without_time",
            Severity.ERROR,
            "precisão indicada sem tempo do acontecimento",
        )
    if stamp.recorded_at > now + CLOCK_SKEW:
        add("recorded_in_future", Severity.ERROR, "registo com data futura")
    if stamp.executed_at is not None and stamp.executed_at > now + CLOCK_SKEW:
        add("executed_in_future", Severity.ERROR, "execução com data futura")
    if stamp.observed_at is not None:
        if stamp.observed_at > stamp.recorded_at + CLOCK_SKEW:
            add("recorded_before_observed", Severity.ERROR, "registado antes de ser observado")
        if stamp.event_time is not None and stamp.observed_at < stamp.event_time:
            add(
                "observed_before_event",
                Severity.WARNING,
                "observação anterior ao acontecimento; confirmar se é uma previsão",
            )
    if (
        stamp.forecast_window is not None
        and stamp.forecast_window.end is not None
        and stamp.forecast_window.end <= stamp.recorded_at
    ):
        add(
            "retrospective_forecast",
            Severity.WARNING,
            "a janela da previsão já tinha terminado quando foi registada (risco de leakage)",
        )
    return issues
