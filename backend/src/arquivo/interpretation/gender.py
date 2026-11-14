"""Deteção de formas com género referidas a quem lê e de planetas com o género errado."""

import re

_COPULA = (
    r"(?:és|estás|ficas|pareces|seres|estares|ficares|pareceres|"
    r"(?:sentes|sentir|sentires|tornas|tornar|tornares|mostras|mostrar|manténs|manter|"
    r"vês|ver|encontras|encontrar|descobres|descobrir|revelas|revelar)-te|"
    r"te\s+(?:sentes|sentires|tornas|tornares|mostras|manténs|vês|encontras|descobres|revelas)|"
    r"(?:podes|deves|mereces|consegues|queres|precisas\s+de|tens\s+de|deixas\s+de|"
    r"merecer|poder|precisar\s+de|deixar\s+de)\s+(?:ser|estar|ficar|parecer))"
)
_ADVERBS = (
    r"(?:(?:mais|muito|tão|bem|demasiado|sobretudo|ainda|já|sempre|realmente|profundamente|"
    r"verdadeiramente|cada\s+vez\s+mais|um\s+pouco|menos)\s+)*"
)
_GENDERED_SUFFIX = (
    r"\w+(?:[aeiouíú]d[oa]s?|os[oa]s?|iv[oa]s?|eir[oa]s?|inh[oa]s?|dor(?:a|es|as)?|ic[oa]s?)"
)
_GENDERED_STEMS = (
    "pront",
    "atent",
    "abert",
    "satisfeit",
    "sozinh",
    "pres",
    "cert",
    "complet",
    "perfeit",
    "sujeit",
    "dispost",
    "expost",
    "convict",
    "seren",
    "tranquil",
    "segur",
    "absort",
    "libert",
    "despert",
    "inteir",
    "plen",
    "sincer",
    "honest",
    "just",
    "pront",
    "lind",
    "bel",
    "fort",
    "fri",
    "quiet",
    "ansios",
    "conscient",
    "envolvid",
    "unid",
    "junt",
    "dign",
    "nov",
    "sábi",
)
_GENDERED_WORD = rf"(?:{_GENDERED_SUFFIX}|(?:{'|'.join(sorted(set(_GENDERED_STEMS)))})[oa]s?)"
_NOT_ADJECTIVE = r"(?!(?:cada|nada|vida|ainda|tudo|fonte|demasiado|sobretudo)\b)"

_ADDRESSED = re.compile(rf"(?i)(?<!\w){_COPULA}\s+{_ADVERBS}{_NOT_ADJECTIVE}{_GENDERED_WORD}(?!\w)")
_SPLIT_FORM = re.compile(r"(?i)\w\((?:a|o|as|os)\)|\((?:a|o)\)|\w/(?:a|o)(?!\w)|\w@(?!\w)")
_FEMININE_BODY_AS_MASCULINE = re.compile(
    r"(?<!\w)(?i:o|do|no|ao|pelo|um|teu|seu)\s+(?:(?i:teu|seu)\s+)?(?:Vénus|Lua)(?!\w)"
)
_MASCULINE_BODY_AS_FEMININE = re.compile(
    r"(?<!\w)(?i:da|na|à|pela|uma|tua|sua)\s+(?:(?i:tua|sua)\s+)?"
    r"(?:Sol|Mercúrio|Marte|Júpiter|Saturno|Úrano|Neptuno|Plutão|Quíron|Nodo Norte|Nodo Sul|"
    r"Ascendente|Meio do Céu)(?!\w)"
)
_REFLEXIVE = re.compile(r"(?i)(?<!\w)(?:ti|tu|contigo)\s+(?:mesm|própri)[oa]s?(?!\w)")
_PATTERNS = (
    _ADDRESSED,
    _SPLIT_FORM,
    _REFLEXIVE,
    _FEMININE_BODY_AS_MASCULINE,
    _MASCULINE_BODY_AS_FEMININE,
)


_NOUN_SERES = re.compile(
    r"(?i)(?<!\w)(?:os|dos|aos|pelos|nos|teus|seus|outros|uns|estes|esses|aqueles|todos)\s+$"
)


def _is_noun_seres(text: str, match: re.Match[str]) -> bool:
    return match.group(0).lower().startswith("seres") and bool(
        _NOUN_SERES.search(text, 0, match.start())
    )


def gendered_forms(text: str) -> list[str]:
    return sorted(
        {
            match.group(0)
            for pattern in _PATTERNS
            for match in pattern.finditer(text)
            if not (pattern is _ADDRESSED and _is_noun_seres(text, match))
        }
    )
