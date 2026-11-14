import json
from datetime import UTC, date, datetime
from types import SimpleNamespace

import pytest

from arquivo.config import Settings
from arquivo.interpretation import gender, guard
from arquivo.interpretation.facts import natal_facts
from arquivo.interpretation.model import (
    AnthropicModel,
    InterpretationMisconfigured,
    InterpretationUnavailable,
)
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

    def __init__(self, *responses: str | Exception) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[str, str, int]] = []

    def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
        self.calls.append((system, prompt, max_tokens))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_anthropic_model_omits_temperature_and_uses_240_second_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client_options: dict[str, object] = {}
    request: dict[str, object] = {}
    fake_client = SimpleNamespace()

    def create(**kwargs: object) -> SimpleNamespace:
        request.update(kwargs)
        return SimpleNamespace(
            content=[
                SimpleNamespace(type="text", text="Leitura "),
                SimpleNamespace(type="image"),
                SimpleNamespace(type="text", text="simbólica"),
            ]
        )

    fake_client.messages = SimpleNamespace(create=create)

    def make_client(**kwargs: object) -> SimpleNamespace:
        client_options.update(kwargs)
        return fake_client

    monkeypatch.setattr("arquivo.interpretation.model.anthropic.Anthropic", make_client)
    model = AnthropicModel("test-key", "claude-sonnet-5-5")
    assert model.complete("sistema", "prompt", max_tokens=42) == "Leitura simbólica"
    assert "temperature" not in request
    assert "extra_body" not in request
    assert client_options["timeout"] == 240.0


@pytest.fixture(scope="module")
def chart() -> NatalChart:
    return calculate_chart(INSTANT, *LISBON)


def natal_json(text: str = "Sol") -> str:
    return json.dumps(
        {"secoes": [{"id": identifier, "texto": text} for identifier, _, _ in NATAL_SECTIONS]}
    )


def daily_sky(
    *,
    revelations: list[Revelation] | None = None,
    tomorrow: Revelation | None = None,
) -> DailySky:
    day = date(2026, 11, 14)
    return DailySky(
        date=day,
        zone="Europe/Lisbon",
        day_starts=datetime(2026, 11, 14, tzinfo=UTC),
        day_ends=datetime(2026, 11, 15, tzinfo=UTC),
        revelations=revelations or [],
        tomorrow=tomorrow,
        active=[],
        upcoming=[],
        events=[],
        calculation=TransitCalculation(orbs={}, aspects=[]),
    )


def daily_json(
    *,
    revelations: list[dict[str, str]] | None = None,
    theme: str | None = "Tema do dia",
    tomorrow: str | None = None,
) -> str:
    return json.dumps(
        {
            "tema": theme,
            "revelacoes": revelations
            if revelations is not None
            else [{"titulo": "Convite à pausa", "texto": "Marte", "pergunta": "O que observas?"}],
            "amanha": tomorrow,
        }
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


@pytest.mark.parametrize(
    "text",
    [
        "O teu Vénus em Carneiro",
        "estás pronto",
        "estás pronta",
        "Podes parecer observador, atento",
        "Podes sentir-te atraído",
        "merecer ser amado",
        "seres autêntico",
        "seres transformado",
        "sentes-te expandido",
        "tua(o)",
        "estás cada vez mais ligada",
        "a tua Marte",
        "és único",
        "sem pedires justificação a ti mesmo",
        "tu própria",
    ],
)
def test_gendered_forms_detects_gendered_references(text: str) -> None:
    assert gender.gendered_forms(text)


@pytest.mark.parametrize(
    "text",
    [
        "sentes-te em expansão",
        "tens tendência a",
        "a tua Vénus em Carneiro",
        "o teu Sol",
        "estás cada vez mais perto",
        "és capaz",
        "estás em casa",
        "ficas a saber",
        "isto pode ser cansativo",
        "tens um olhar observador",
        "como te sentes hoje",
        "a Lua em Escorpião",
        "és tu quem",
        "estás ainda mais livre",
        "és fonte de luz",
        "dá forma a Saturno",
        "mereces amor",
        "és alguém sensível",
        "sentes-te inteiramente presente",
        "estás demasiado perto",
        "és sobretudo alguém sensível",
        "Cultiva o afeto pelos teus seres queridos",
        "os seres vivos à tua volta",
    ],
)
def test_gendered_forms_ignores_neutral_references(text: str) -> None:
    assert gender.gendered_forms(text) == []


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
    assert model.calls[0][2] == 12000


def test_natal_retries_gendered_text_with_feedback(chart: NatalChart) -> None:
    model = FakeModel(natal_json("estás pronto"), natal_json("Sol"))
    sections = interpret_natal(chart, model)
    assert len(model.calls) == 2
    assert all(section.text == "Sol" for section in sections)
    assert "A tua resposta anterior foi rejeitada" in model.calls[1][1]
    assert "estás pronto" in model.calls[1][1]


def test_natal_retries_transient_error_with_original_prompt(chart: NatalChart) -> None:
    model = FakeModel(
        InterpretationUnavailable("indisponibilidade temporária"),
        natal_json(),
    )
    interpret_natal(chart, model)
    assert len(model.calls) == 2
    assert model.calls[1][1] == model.calls[0][1]


def test_natal_retries_guard_violations_three_times(chart: NatalChart) -> None:
    model = FakeModel(*(natal_json("Lilith") for _ in range(3)))
    with pytest.raises(InterpretationUnavailable):
        interpret_natal(chart, model)
    assert len(model.calls) == 3


def test_natal_does_not_retry_misconfigured_model(chart: NatalChart) -> None:
    class MisconfiguredFakeModel:
        name = "fake-claude"

        def __init__(self) -> None:
            self.calls = 0

        def complete(self, system: str, prompt: str, *, max_tokens: int) -> str:
            self.calls += 1
            raise InterpretationMisconfigured("configuração inválida")

    model = MisconfiguredFakeModel()
    with pytest.raises(InterpretationMisconfigured):
        interpret_natal(chart, model)
    assert model.calls == 1


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
        daily_json(revelations=[], theme=None),
        daily_json(
            revelations=[
                {"titulo": "Ritmo e estrutura", "texto": "Saturno", "pergunta": "O que observas?"}
            ]
        ),
    )
    reading = interpret_day(sky, chart, model)
    assert reading.theme == "Tema do dia"
    assert reading.revelations[0].title == "Ritmo e estrutura"
    assert reading.revelations[0].text == "Saturno"
    assert len(model.calls) == 2
    assert "exato a 14/11 às 14:32" in model.calls[0][1]
    assert model.calls[0][2] == 6000


def test_day_accepts_structured_revelation_and_strips_fields(chart: NatalChart) -> None:
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime(2026, 11, 14, 11, tzinfo=UTC),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    sky = daily_sky(revelations=[Revelation(weight=1, event=event)])
    response = daily_json(
        theme="  Tema do dia  ",
        revelations=[
            {
                "titulo": "  Ritmo e estrutura  ",
                "texto": "  Marte  ",
                "pergunta": "  O que observas?  ",
            }
        ],
    )
    reading = interpret_day(sky, chart, FakeModel(response))
    assert reading.theme == "Tema do dia"
    assert reading.revelations[0].title == "Ritmo e estrutura"
    assert reading.revelations[0].text == "Marte"
    assert reading.revelations[0].question == "O que observas?"


def test_day_retries_gendered_text_with_feedback(chart: NatalChart) -> None:
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime(2026, 11, 14, 11, tzinfo=UTC),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    sky = daily_sky(revelations=[Revelation(weight=1, event=event)])
    model = FakeModel(
        daily_json(
            revelations=[
                {
                    "titulo": "Convite à pausa",
                    "texto": "estás pronto",
                    "pergunta": "O que observas?",
                }
            ]
        ),
        daily_json(),
    )
    reading = interpret_day(sky, chart, model)
    assert reading.revelations[0].text == "Marte"
    assert len(model.calls) == 2
    assert "A tua resposta anterior foi rejeitada" in model.calls[1][1]
    assert "estás pronto" in model.calls[1][1]


def test_day_retries_transient_error_with_original_prompt(chart: NatalChart) -> None:
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime(2026, 11, 14, 11, tzinfo=UTC),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    sky = daily_sky(revelations=[Revelation(weight=1, event=event)])
    model = FakeModel(
        InterpretationUnavailable("indisponibilidade temporária"),
        daily_json(),
    )
    interpret_day(sky, chart, model)
    assert len(model.calls) == 2
    assert model.calls[1][1] == model.calls[0][1]


def test_day_retries_non_null_tomorrow_when_no_tomorrow_exists(chart: NatalChart) -> None:
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime(2026, 11, 14, 11, tzinfo=UTC),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    sky = daily_sky(revelations=[Revelation(weight=1, event=event)])
    model = FakeModel(
        daily_json(tomorrow="Sol"),
        daily_json(),
    )
    assert interpret_day(sky, chart, model).tomorrow is None
    assert len(model.calls) == 2
    assert "Marte entra em Sagitário" in model.calls[0][1]


@pytest.mark.parametrize("field", ["tema", "titulo", "pergunta"])
def test_day_retries_gendered_field_with_feedback(chart: NatalChart, field: str) -> None:
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime(2026, 11, 14, 11, tzinfo=UTC),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    sky = daily_sky(revelations=[Revelation(weight=1, event=event)])
    invalid = {"titulo": "Convite à pausa", "texto": "Saturno", "pergunta": "O que observas?"}
    if field != "tema":
        invalid[field] = "estás pronto"
    model = FakeModel(
        daily_json(
            revelations=[invalid], theme="estás pronto" if field == "tema" else "Tema do dia"
        ),
        daily_json(),
    )
    result = interpret_day(sky, chart, model)
    assert result.revelations[0].title == "Convite à pausa"
    assert len(model.calls) == 2
    assert "A tua resposta anterior foi rejeitada" in model.calls[1][1]
    assert "estás pronto" in model.calls[1][1]


def test_day_rejects_extra_fields_with_retry(chart: NatalChart) -> None:
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime(2026, 11, 14, 11, tzinfo=UTC),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    sky = daily_sky(revelations=[Revelation(weight=1, event=event)])
    invalid = json.loads(daily_json())
    invalid["surpresa"] = "campo extra"
    model = FakeModel(json.dumps(invalid), daily_json())
    result = interpret_day(sky, chart, model)
    assert result.theme == "Tema do dia"
    assert len(model.calls) == 2


def test_day_rejects_non_null_theme_without_revelations(chart: NatalChart) -> None:
    event = SkyEvent(
        kind=EventKind.SIGN_INGRESS,
        at=datetime(2026, 11, 15, 11, tzinfo=UTC),
        body=Body.MARS,
        sign=Sign.SAGITTARIUS,
    )
    sky = daily_sky(tomorrow=Revelation(weight=1, event=event))
    model = FakeModel(
        daily_json(revelations=[], theme="Tema do dia", tomorrow="Uma pista."),
        daily_json(revelations=[], theme=None, tomorrow="Uma pista."),
    )
    result = interpret_day(sky, chart, model)
    assert result.theme is None
    assert result.revelations == []
    assert len(model.calls) == 2


def test_day_with_no_revelations_and_no_tomorrow_does_not_call_model(
    chart: NatalChart,
) -> None:
    model = FakeModel()
    assert interpret_day(daily_sky(), chart, model).theme is None
    assert interpret_day(daily_sky(), chart, model).revelations == []
    assert model.calls == []
