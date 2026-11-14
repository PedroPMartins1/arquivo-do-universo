import json
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from arquivo.config import Settings
from arquivo.interpretation import guard
from arquivo.interpretation.facts import natal_facts
from arquivo.interpretation.model import AnthropicModel, InterpretationUnavailable
from arquivo.interpretation.prompts import NATAL_SECTIONS
from arquivo.interpretation.service import interpret_day, interpret_natal
from arquivo.natal.chart import NatalChart, calculate_chart
from arquivo.natal.settings import AspectKind, Body, Sign
from arquivo.transits.engine import (
    DailySky,
    EventKind,
    Revelation,
    SkyEvent,
    Transit,
    TransitCalculation,
)

INSTANT = datetime(1993, 5, 20, 12, 35, tzinfo=UTC)
LISBON = (38.7223, -9.1393)


class FakeModel:
    name = "fake-claude"

    def __init__(self, *responses: str) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, int]] = []

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
        self.calls.append((system, prompt, max_tokens))
        return self.responses.pop(0)


def test_anthropic_model_passes_temperature_and_concatenates_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = AnthropicModel("test-key", "claude-sonnet-5-5")
    request: dict[str, object] = {}

    def create(**kwargs: object) -> SimpleNamespace:
        request.update(kwargs)
        return SimpleNamespace(
            content=[
                SimpleNamespace(type="text", text="Leitura "),
                SimpleNamespace(type="image"),
                SimpleNamespace(type="text", text="simbólica"),
            ]
        )

    monkeypatch.setattr(model._client.messages, "create", create)
    assert model.complete("sistema", "prompt", max_tokens=42) == "Leitura simbólica"
    assert request["extra_body"] == {"temperature": 0.8}


@pytest.fixture(scope="module")
def chart() -> NatalChart:
    return calculate_chart(INSTANT, *LISBON)


def natal_json(text: str = "Sol") -> str:
    return json.dumps(
        {"secoes": [{"id": identifier, "texto": text} for identifier, _, _ in NATAL_SECTIONS]}
    )


def daily_sky(*, revelations: list[Revelation] | None = None) -> DailySky:
    day = date(2026, 11, 14)
    return DailySky(
        date=day,
        zone="Europe/Lisbon",
        day_starts=datetime(2026, 11, 14, tzinfo=UTC),
        day_ends=datetime(2026, 11, 15, tzinfo=UTC),
        revelations=revelations or [],
        tomorrow=None,
        active=[],
        upcoming=[],
        events=[],
        calculation=TransitCalculation(orbs={}, aspects=[]),
    )


def test_natal_facts_and_prompt_do_not_include_birth_or_account_data(chart: NatalChart) -> None:
    model = FakeModel(natal_json())
    interpret_natal(chart, model)
    facts = natal_facts(chart)
    prompt = model.calls[0][1]
    for private_value in (
        "1993-05-20",
        "12:35",
        "Lisboa",
        "38.7223",
        "-9.1393",
        "instant_utc",
        "ana@example.org",
    ):
        assert private_value not in facts
        assert private_value not in prompt
    assert "julian_day" not in prompt


def test_guard_accepts_only_present_labels_and_rejects_unknown_points() -> None:
    assert guard.check("Sol em Carneiro, em Quadratura.", {"Sol", "Carneiro", "Quadratura"}) == []
    assert guard.check("Lilith", {"Lilith"}) == ["Lilith"]
    assert guard.check("Plutão", set()) == ["Plutão"]
    assert guard.check("o sol aquece a Lua", {"Lua"}) == []
    assert guard.check("Nodo Sul", set()) == ["Nodo Sul"]
    assert guard.check("Nodo Sul", {"Nodo Norte"}) == []


def test_anthropic_key_aliases_and_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARQUIVO_ANTHROPIC_API_KEY", "local-test-key")
    settings = Settings(_env_file=None)
    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == "local-test-key"
    assert settings.anthropic_model == "claude-sonnet-5-5"
    monkeypatch.delenv("ARQUIVO_ANTHROPIC_API_KEY")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "alias-test-key")
    settings = Settings(_env_file=None)
    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == "alias-test-key"


def test_natal_json_returns_ordered_named_sections(chart: NatalChart) -> None:
    sections = interpret_natal(chart, FakeModel(natal_json()))
    assert [(section.id, section.title) for section in sections] == [
        (identifier, title) for identifier, title, _ in NATAL_SECTIONS
    ]


def test_natal_retries_invalid_json(chart: NatalChart) -> None:
    model = FakeModel("isto não é JSON", natal_json())
    assert len(interpret_natal(chart, model)) == 6
    assert len(model.calls) == 2
    assert model.calls[0][2] == 4000


def test_natal_retries_guard_violations_three_times(chart: NatalChart) -> None:
    model = FakeModel(*(natal_json("Lilith") for _ in range(3)))
    with pytest.raises(InterpretationUnavailable):
        interpret_natal(chart, model)
    assert len(model.calls) == 3


def test_natal_retries_sections_in_the_wrong_order(chart: NatalChart) -> None:
    invalid = json.dumps(
        {
            "secoes": [
                {"id": identifier, "texto": "Sol"} for identifier, _, _ in reversed(NATAL_SECTIONS)
            ]
        }
    )
    model = FakeModel(invalid, natal_json())
    assert len(interpret_natal(chart, model)) == 6
    assert len(model.calls) == 2


def test_day_retries_when_revelation_count_is_wrong(chart: NatalChart) -> None:
    transit = Transit(
        body=Body.SATURN,
        natal_point=Body.JUPITER,
        kind=AspectKind.SQUARE,
        allowed_orb=1,
        starts=None,
        ends=None,
        exact=[datetime(2026, 11, 14, 14, 32, tzinfo=UTC)],
        orb=0.4,
        applying=True,
        natal_house=5,
    )
    sky = daily_sky(revelations=[Revelation(weight=1, transit=transit)])
    model = FakeModel(
        json.dumps({"revelacoes": [], "amanha": None}),
        json.dumps({"revelacoes": ["Saturno"], "amanha": None}),
    )
    reading = interpret_day(sky, chart, model)
    assert reading.revelations == ["Saturno"]
    assert len(model.calls) == 2
    assert "exato a 14/11 às 14:32" in model.calls[0][1]
    assert model.calls[0][2] == 2500


def test_day_retries_non_null_tomorrow_when_no_tomorrow_exists(chart: NatalChart) -> None:
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime(2026, 11, 14, 11, tzinfo=UTC),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    sky = daily_sky(revelations=[Revelation(weight=1, event=event)])
    model = FakeModel(
        json.dumps({"revelacoes": ["Marte"], "amanha": "Sol"}),
        json.dumps({"revelacoes": ["Marte"], "amanha": None}),
    )
    assert interpret_day(sky, chart, model).tomorrow is None
    assert len(model.calls) == 2
    assert "Marte entra em Sagitário" in model.calls[0][1]


def test_day_with_no_revelations_and_no_tomorrow_does_not_call_model(
    chart: NatalChart,
) -> None:
    model = FakeModel()
    assert interpret_day(daily_sky(), chart, model).revelations == []
    assert model.calls == []
