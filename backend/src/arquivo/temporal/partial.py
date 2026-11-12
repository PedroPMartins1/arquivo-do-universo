"""Datas incompletas ou aproximadas, sem inventar componentes em falta (dossiê §18.2, §51)."""

import calendar
import re
from datetime import date, timedelta
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from arquivo.temporal.precision import TemporalPrecision

_PATTERN = re.compile(r"^(?P<year>\d{4})(-(?P<month>\d{2})(-(?P<day>\d{2}))?)?$")


class PartialDate(BaseModel):
    model_config = ConfigDict(frozen=True)

    year: int = Field(ge=1, le=9999)
    month: int | None = Field(default=None, ge=1, le=12)
    day: int | None = Field(default=None, ge=1, le=31)
    approximate: bool = False
    calendar: Literal["gregorian"] = "gregorian"

    @model_validator(mode="after")
    def _check(self) -> Self:
        if self.day is not None:
            if self.month is None:
                raise ValueError("um dia exige mês")
            if self.day > calendar.monthrange(self.year, self.month)[1]:
                raise ValueError("dia inválido para o mês")
        return self

    @classmethod
    def parse(cls, text: str, *, approximate: bool = False) -> "PartialDate":
        match = _PATTERN.fullmatch(text.strip())
        if match is None:
            raise ValueError("formato esperado: AAAA, AAAA-MM ou AAAA-MM-DD")
        return cls(
            year=int(match["year"]),
            month=int(match["month"]) if match["month"] else None,
            day=int(match["day"]) if match["day"] else None,
            approximate=approximate,
        )

    @property
    def precision(self) -> TemporalPrecision:
        if self.day is not None:
            return TemporalPrecision.DAY
        if self.month is not None:
            return TemporalPrecision.MONTH
        return TemporalPrecision.YEAR

    def bounds(self) -> tuple[date, date]:
        """Intervalo semiaberto [início, fim) dos dias compatíveis com o que é conhecido."""
        if self.day is not None:
            assert self.month is not None
            start = date(self.year, self.month, self.day)
            return start, start + timedelta(days=1)
        if self.month is not None:
            start = date(self.year, self.month, 1)
            last = calendar.monthrange(self.year, self.month)[1]
            return start, start + timedelta(days=last)
        return date(self.year, 1, 1), date(self.year + 1, 1, 1)

    def __str__(self) -> str:
        text = f"{self.year:04d}"
        if self.month is not None:
            text += f"-{self.month:02d}"
        if self.day is not None:
            text += f"-{self.day:02d}"
        return f"c. {text}" if self.approximate else text
