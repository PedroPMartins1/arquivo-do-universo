"""Dados de nascimento: a data e a hora têm de ser exatas (decisão D-020).

Exato significa: data completa, hora ao minuto, local conhecido, sem margem de incerteza e um
único instante UTC. Uma hora repetida na mudança de hora só é aceite se o utilizador indicar qual
das duas ocorrências foi; uma hora inexistente é rejeitada.
"""

from dataclasses import dataclass
from datetime import date, datetime, time

from arquivo.temporal.local_time import (
    LocalTimeResolution,
    ResolutionStatus,
    resolve_local_time,
)


class InexactBirthDataError(ValueError):
    """Os dados de nascimento não identificam um único instante."""


@dataclass(frozen=True)
class BirthInstant:
    utc: datetime
    utc_offset_seconds: int
    abbreviation: str | None
    zone: str
    resolution: LocalTimeResolution


def resolve_birth_instant(
    birth_date: date,
    birth_time: time,
    zone: str,
    *,
    occurrence: int | None = None,
) -> BirthInstant:
    """`occurrence` (0 ou 1) só é usado quando a hora local acontece duas vezes."""
    if birth_time.tzinfo is not None:
        raise InexactBirthDataError("a hora de nascimento é hora local, sem fuso")
    if birth_time.second or birth_time.microsecond:
        raise InexactBirthDataError("a hora de nascimento regista-se ao minuto")

    resolution = resolve_local_time(datetime.combine(birth_date, birth_time), zone)
    if resolution.status is ResolutionStatus.NONEXISTENT:
        raise InexactBirthDataError(
            f"{birth_date} {birth_time:%H:%M} não existiu em {zone} (mudança de hora)"
        )
    if resolution.status is ResolutionStatus.AMBIGUOUS:
        if occurrence not in (0, 1):
            raise InexactBirthDataError(
                f"{birth_date} {birth_time:%H:%M} aconteceu duas vezes em {zone}: "
                "indicar a primeira (0) ou a segunda (1) ocorrência"
            )
        candidate = resolution.candidates[occurrence]
    else:
        candidate = resolution.candidates[0]

    return BirthInstant(
        utc=candidate.utc,
        utc_offset_seconds=candidate.utc_offset_seconds,
        abbreviation=candidate.abbreviation,
        zone=zone,
        resolution=resolution,
    )
