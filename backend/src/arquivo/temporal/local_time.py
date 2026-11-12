"""Conversão de hora local (de parede) para UTC, sem esconder ambiguidade nem incerteza."""

from datetime import UTC, datetime, timedelta
from enum import StrEnum

from pydantic import AwareDatetime, BaseModel, ConfigDict, NaiveDatetime

from arquivo.temporal.zones import TZDATA_VERSION, load_zone

IANA_RELIABLE_FROM_YEAR = 1970


class ResolutionStatus(StrEnum):
    UNIQUE = "unique"
    AMBIGUOUS = "ambiguous"
    NONEXISTENT = "nonexistent"


class UtcCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    utc: AwareDatetime
    utc_offset_seconds: int
    abbreviation: str | None
    fold: int


class LocalTimeResolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    local: NaiveDatetime
    zone: str
    status: ResolutionStatus
    candidates: tuple[UtcCandidate, ...]
    uncertainty_minutes: int
    earliest_utc: AwareDatetime
    latest_utc: AwareDatetime
    tzdata_version: str
    warnings: tuple[str, ...]


def resolve_local_time(
    local: datetime, zone: str, *, uncertainty_minutes: int = 0
) -> LocalTimeResolution:
    """Resolve uma hora local num fuso IANA.

    Horas repetidas (fim do horário de verão) devolvem dois candidatos; horas inexistentes (início
    do horário de verão) devolvem as duas interpretações possíveis. Nenhuma é escolhida em silêncio.
    """
    if local.tzinfo is not None:
        raise ValueError("a hora local não pode ter fuso associado")
    if uncertainty_minutes < 0:
        raise ValueError("a incerteza não pode ser negativa")

    tz = load_zone(zone)
    interpretations: list[tuple[UtcCandidate, bool]] = []
    for fold in (0, 1):
        aware = local.replace(tzinfo=tz, fold=fold)
        utc = aware.astimezone(UTC)
        offset = aware.utcoffset()
        assert offset is not None
        exists = utc.astimezone(tz).replace(tzinfo=None) == local
        candidate = UtcCandidate(
            utc=utc,
            utc_offset_seconds=int(offset.total_seconds()),
            abbreviation=aware.tzname(),
            fold=fold,
        )
        if all(c.utc != utc for c, _ in interpretations):
            interpretations.append((candidate, exists))

    warnings: list[str] = []
    valid = [c for c, exists in interpretations if exists]
    if len(valid) == 1:
        status, candidates = ResolutionStatus.UNIQUE, valid
    elif len(valid) == 2:
        status, candidates = ResolutionStatus.AMBIGUOUS, valid
        warnings.append(
            "Hora local repetida (mudança de hora): existem dois instantes UTC possíveis."
        )
    else:
        status, candidates = ResolutionStatus.NONEXISTENT, [c for c, _ in interpretations]
        warnings.append(
            "Hora local inexistente neste fuso (salto da mudança de hora): são apresentadas as "
            "duas interpretações possíveis."
        )

    if local.year < IANA_RELIABLE_FROM_YEAR:
        warnings.append(
            "A base IANA só garante exatidão a partir de 1970. Confirmar o fuso e a hora legal "
            "com uma fonte histórica."
        )

    candidates = sorted(candidates, key=lambda c: c.utc)
    margin = timedelta(minutes=uncertainty_minutes)
    return LocalTimeResolution(
        local=local,
        zone=zone,
        status=status,
        candidates=tuple(candidates),
        uncertainty_minutes=uncertainty_minutes,
        earliest_utc=candidates[0].utc - margin,
        latest_utc=candidates[-1].utc + margin,
        tzdata_version=TZDATA_VERSION,
        warnings=tuple(warnings),
    )
