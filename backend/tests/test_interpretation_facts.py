from datetime import UTC, datetime

from arquivo.interpretation.facts import natal_facts
from arquivo.natal.chart import calculate_chart
from arquivo.natal.labels import label
from arquivo.natal.settings import Sign


def test_natal_facts_truncate_body_angle_and_house_cusp_degrees() -> None:
    chart = calculate_chart(datetime(1993, 5, 20, 12, 35, tzinfo=UTC), 38.7223, -9.1393)
    body = chart.bodies[0].model_copy(update={"degree_in_sign": 29.7})
    ascendant_longitude = chart.angles.ascendant - chart.angles.ascendant % 30 + 29.7
    angles = chart.angles.model_copy(update={"ascendant": ascendant_longitude})
    cusp = chart.houses[0].model_copy(update={"degree_in_sign": 29.7})
    chart = chart.model_copy(
        update={
            "bodies": [body, *chart.bodies[1:]],
            "angles": angles,
            "houses": [cusp, *chart.houses[1:]],
        }
    )

    facts = natal_facts(chart).splitlines()

    assert any(line.startswith(f"{label(body.body)} em {label(body.sign)} 29°") for line in facts)
    assert f"Ascendente em {label(Sign.of(ascendant_longitude))} 29°" in facts
    assert f"Cúspide da casa {cusp.house} em {label(cusp.sign)} 29°" in facts
