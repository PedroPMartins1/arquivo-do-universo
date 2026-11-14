import re
from collections.abc import Iterable

from arquivo.natal.labels import label
from arquivo.natal.settings import AspectKind, Body, Sign

_VOCABULARY = {
    *(label(value) for value in Body),
    *(label(value) for value in Sign),
    *(label(value) for value in AspectKind),
    "Ascendente",
    "Meio do Céu",
}
_ALWAYS_FORBIDDEN = {
    "Lilith",
    "Ceres",
    "Juno",
    "Vesta",
    "Palas",
    "Eris",
    "Parte da Fortuna",
}


def _find_terms(text: str, terms: Iterable[str]) -> set[str]:
    return {
        term for term in terms if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text) is not None
    }


def allowed_labels(facts: str) -> set[str]:
    return _find_terms(facts, _VOCABULARY)


def check(text: str, allowed: set[str]) -> list[str]:
    found = _find_terms(text, _VOCABULARY)
    forbidden = _find_terms(text, _ALWAYS_FORBIDDEN)
    if "Nodo Norte" not in allowed:
        forbidden.update(_find_terms(text, {"Nodo Sul"}))
    return sorted((found - allowed) | forbidden)
