import pytest

from arquivo.core.epistemics import (
    EpistemicClass,
    EpistemicViolation,
    KnowledgeDomain,
    classification_issues,
    reclassification_issues,
    validate_classification,
)
from arquivo.core.provenance import Provenance, ProvenanceOrigin


def test_documented_fact_requires_source() -> None:
    issues = classification_issues(
        EpistemicClass.DOCUMENTED_FACT, KnowledgeDomain.PERSONAL, metadata=set()
    )
    assert issues == ["a classe 'documented_fact' exige: ['source']"]


def test_inference_requires_method_and_assumptions() -> None:
    with pytest.raises(EpistemicViolation) as error:
        validate_classification(EpistemicClass.INFERENCE, KnowledgeDomain.GENERAL, {"method"})
    assert "assumptions" in str(error.value)


@pytest.mark.parametrize(
    "epistemic_class",
    [
        EpistemicClass.DOCUMENTED_FACT,
        EpistemicClass.EMPIRICAL_EVIDENCE,
        EpistemicClass.PREDICTION,
        EpistemicClass.INFERENCE,
        EpistemicClass.HYPOTHESIS,
    ],
)
def test_astrology_cannot_claim_scientific_authority(epistemic_class: EpistemicClass) -> None:
    everything = {"source", "method", "assumptions", "framework", "horizon", "model", "uncertainty"}
    issues = classification_issues(epistemic_class, KnowledgeDomain.ASTROLOGY, everything)
    assert any("astrology" in issue for issue in issues)


def test_astrological_interpretation_requires_framework() -> None:
    validate_classification(EpistemicClass.INTERPRETATION, KnowledgeDomain.ASTROLOGY, {"framework"})
    with pytest.raises(EpistemicViolation):
        validate_classification(EpistemicClass.INTERPRETATION, KnowledgeDomain.ASTROLOGY, set())


def test_inference_is_not_promoted_to_fact_without_new_source() -> None:
    assert reclassification_issues(
        EpistemicClass.INFERENCE, EpistemicClass.DOCUMENTED_FACT, has_new_source=False
    )
    assert not reclassification_issues(
        EpistemicClass.INFERENCE, EpistemicClass.DOCUMENTED_FACT, has_new_source=True
    )
    assert not reclassification_issues(
        EpistemicClass.DOCUMENTED_FACT, EpistemicClass.HYPOTHESIS, has_new_source=False
    )


def test_provenance_satisfies_source_and_method() -> None:
    provenance = Provenance(
        origin=ProvenanceOrigin.DOCUMENTED, provided_by="u", source_id="s", method="m"
    )
    assert provenance.metadata_keys() == {"source", "method"}


def test_every_class_has_portuguese_label() -> None:
    assert {c.label_pt for c in EpistemicClass} >= {"Facto documentado", "Previsão"}
