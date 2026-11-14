import hashlib
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from arquivo.interpretation import guard
from arquivo.interpretation.facts import daily_facts, natal_facts, revelation_facts
from arquivo.interpretation.model import (
    InterpretationMisconfigured,
    InterpretationUnavailable,
    TextModel,
)
from arquivo.interpretation.prompts import DAY, NATAL, NATAL_SECTIONS, SYSTEM
from arquivo.natal.chart import NatalChart
from arquivo.natal.labels import label
from arquivo.transits.engine import DailySky


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    text: str


@dataclass(frozen=True)
class DayReading:
    revelations: list[str]
    tomorrow: str | None


class _NatalSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    texto: str

    @field_validator("id", "texto")
    @classmethod
    def _nonempty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("o campo não pode estar vazio")
        return value


class _NatalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    secoes: list[_NatalSection]


class _DayResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revelacoes: list[str]
    amanha: str | None

    @field_validator("revelacoes")
    @classmethod
    def _nonempty_revelations(cls, values: list[str]) -> list[str]:
        stripped = [value.strip() for value in values]
        if any(not value for value in stripped):
            raise ValueError("as revelações não podem estar vazias")
        return stripped

    @field_validator("amanha")
    @classmethod
    def _nonempty_tomorrow(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("a revelação de amanhã não pode estar vazia")
        return value


def natal_prompt(chart: NatalChart) -> tuple[str, set[str]]:
    facts = natal_facts(chart)
    sections = "\n".join(
        f"- {identifier}: {description}" for identifier, _, description in NATAL_SECTIONS
    )
    prompt = NATAL.format(
        zodiac=label(chart.settings.zodiac),
        house_system=label(chart.settings.house_system),
        facts=facts,
        sections=sections,
    )
    return prompt, guard.allowed_labels(facts)


def day_prompt(sky: DailySky, chart: NatalChart) -> tuple[str, set[str]]:
    facts, tomorrow = daily_facts(sky, chart)
    natal = natal_facts(chart)
    revelation_lines = (
        "\n".join(
            f"{index}. {revelation_facts(revelation, sky.zone, sky.date)}"
            for index, revelation in enumerate(sky.revelations, start=1)
        )
        or "nenhum"
    )
    prompt = DAY.format(
        date=sky.date.isoformat(),
        zone=sky.zone,
        natal=natal,
        revelations=revelation_lines,
        tomorrow=tomorrow or "nenhum",
        count=len(sky.revelations),
    )
    allowed_facts = f"{facts}\n{tomorrow or ''}"
    return prompt, guard.allowed_labels(allowed_facts)


def prompt_hash(system: str, prompt: str) -> str:
    return hashlib.sha256(f"{system}\n\n{prompt}".encode()).hexdigest()


def interpret_natal(chart: NatalChart, model: TextModel) -> list[Section]:
    prompt, allowed = natal_prompt(chart)
    expected_ids = [identifier for identifier, _, _ in NATAL_SECTIONS]
    last_error: Exception | None = None
    for _ in range(3):
        try:
            response = _NatalResponse.model_validate_json(
                model.complete(SYSTEM, prompt, max_tokens=12000)
            )
            sections = response.secoes
            if [section.id for section in sections] != expected_ids:
                raise ValueError("identificadores ou ordem das secções incorretos")
            if len(sections) != len(NATAL_SECTIONS):
                raise ValueError("número de secções incorreto")
            for section in sections:
                violations = guard.check(section.texto, allowed)
                if violations:
                    raise ValueError(f"termos astrológicos não permitidos: {violations}")
            return [
                Section(identifier, title, section.texto)
                for section, (identifier, title, _) in zip(sections, NATAL_SECTIONS, strict=True)
            ]
        except InterpretationMisconfigured:
            raise
        except (InterpretationUnavailable, ValidationError, ValueError) as error:
            last_error = error
    raise InterpretationUnavailable(
        "não foi possível validar a interpretação natal"
    ) from last_error


def interpret_day(sky: DailySky, chart: NatalChart, model: TextModel) -> DayReading:
    if not sky.revelations and sky.tomorrow is None:
        return DayReading([], None)
    prompt, allowed = day_prompt(sky, chart)
    last_error: Exception | None = None
    for _ in range(3):
        try:
            response = _DayResponse.model_validate_json(
                model.complete(SYSTEM, prompt, max_tokens=6000)
            )
            if len(response.revelacoes) != len(sky.revelations):
                raise ValueError("número de revelações incorreto")
            if (response.amanha is None) != (sky.tomorrow is None):
                raise ValueError("presença da revelação de amanhã incorreta")
            texts = [*response.revelacoes, *([response.amanha] if response.amanha else [])]
            for text in texts:
                violations = guard.check(text, allowed)
                if violations:
                    raise ValueError(f"termos astrológicos não permitidos: {violations}")
            return DayReading(response.revelacoes, response.amanha)
        except InterpretationMisconfigured:
            raise
        except (InterpretationUnavailable, ValidationError, ValueError) as error:
            last_error = error
    raise InterpretationUnavailable(
        "não foi possível validar a interpretação diária"
    ) from last_error
