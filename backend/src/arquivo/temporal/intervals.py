from datetime import datetime
from typing import Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, model_validator


class Interval(BaseModel):
    """Intervalo semiaberto [start, end). `None` representa um limite em aberto."""

    model_config = ConfigDict(frozen=True)

    start: AwareDatetime | None = None
    end: AwareDatetime | None = None

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("o início do intervalo tem de ser anterior ao fim")
        return self

    def contains(self, instant: datetime) -> bool:
        if instant.tzinfo is None:
            raise ValueError("o instante tem de ter fuso")
        after_start = self.start is None or self.start <= instant
        before_end = self.end is None or instant < self.end
        return after_start and before_end

    def overlaps(self, other: "Interval") -> bool:
        starts_before_other_ends = self.start is None or other.end is None or self.start < other.end
        other_starts_before_end = other.start is None or self.end is None or other.start < self.end
        return starts_before_other_ends and other_starts_before_end
