"""Classificação epistemológica transversal (dossiê §10–11)."""

from collections.abc import Iterable
from enum import StrEnum


class EpistemicClass(StrEnum):
    DOCUMENTED_FACT = "documented_fact"
    EMPIRICAL_EVIDENCE = "empirical_evidence"
    HYPOTHESIS = "hypothesis"
    INFERENCE = "inference"
    INTERPRETATION = "interpretation"
    PREDICTION = "prediction"
    SPECULATION = "speculation"

    @property
    def label_pt(self) -> str:
        return _LABELS_PT[self]


_LABELS_PT: dict[EpistemicClass, str] = {
    EpistemicClass.DOCUMENTED_FACT: "Facto documentado",
    EpistemicClass.EMPIRICAL_EVIDENCE: "Evidência empírica",
    EpistemicClass.HYPOTHESIS: "Hipótese",
    EpistemicClass.INFERENCE: "Inferência",
    EpistemicClass.INTERPRETATION: "Interpretação",
    EpistemicClass.PREDICTION: "Previsão",
    EpistemicClass.SPECULATION: "Exploração/especulação",
}


class KnowledgeDomain(StrEnum):
    PERSONAL = "personal"
    GENERAL = "general"
    SCIENCE = "science"
    ASTRONOMY = "astronomy"
    ASTROLOGY = "astrology"


REQUIRED_METADATA: dict[EpistemicClass, frozenset[str]] = {
    EpistemicClass.DOCUMENTED_FACT: frozenset({"source"}),
    EpistemicClass.EMPIRICAL_EVIDENCE: frozenset({"source", "method"}),
    EpistemicClass.HYPOTHESIS: frozenset(),
    EpistemicClass.INFERENCE: frozenset({"method", "assumptions"}),
    EpistemicClass.INTERPRETATION: frozenset({"framework"}),
    EpistemicClass.PREDICTION: frozenset({"horizon", "model", "uncertainty"}),
    EpistemicClass.SPECULATION: frozenset(),
}

# §11.2 e §17.6: a astrologia é um sistema simbólico. Os seus conteúdos não podem ter a autoridade
# de facto, evidência ou previsão empírica. As posições calculadas pertencem ao domínio astronómico.
ALLOWED_CLASSES: dict[KnowledgeDomain, frozenset[EpistemicClass]] = {
    KnowledgeDomain.ASTROLOGY: frozenset(
        {EpistemicClass.INTERPRETATION, EpistemicClass.SPECULATION}
    ),
}

_ESTABLISHED = frozenset({EpistemicClass.DOCUMENTED_FACT, EpistemicClass.EMPIRICAL_EVIDENCE})


class EpistemicViolation(ValueError):
    def __init__(self, issues: list[str]) -> None:
        super().__init__("; ".join(issues))
        self.issues = issues


def classification_issues(
    epistemic_class: EpistemicClass,
    domain: KnowledgeDomain,
    metadata: Iterable[str],
) -> list[str]:
    issues: list[str] = []
    allowed = ALLOWED_CLASSES.get(domain)
    if allowed is not None and epistemic_class not in allowed:
        issues.append(
            f"o domínio '{domain}' não admite a classe '{epistemic_class}'; "
            f"classes permitidas: {sorted(allowed)}"
        )
    missing = REQUIRED_METADATA[epistemic_class] - set(metadata)
    if missing:
        issues.append(f"a classe '{epistemic_class}' exige: {sorted(missing)}")
    return issues


def validate_classification(
    epistemic_class: EpistemicClass,
    domain: KnowledgeDomain,
    metadata: Iterable[str],
) -> None:
    issues = classification_issues(epistemic_class, domain, metadata)
    if issues:
        raise EpistemicViolation(issues)


def reclassification_issues(
    previous: EpistemicClass,
    new: EpistemicClass,
    *,
    has_new_source: bool,
) -> list[str]:
    """Uma inferência, hipótese ou interpretação não se torna facto sem nova fonte (§13.5)."""
    if new in _ESTABLISHED and previous not in _ESTABLISHED and not has_new_source:
        return [f"promover '{previous}' a '{new}' exige uma nova fonte que o documente"]
    return []
