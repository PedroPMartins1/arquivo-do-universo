from fastapi import APIRouter
from pydantic import BaseModel

from arquivo.core.epistemics import (
    ALLOWED_CLASSES,
    REQUIRED_METADATA,
    EpistemicClass,
    KnowledgeDomain,
)

router = APIRouter(prefix="/epistemics", tags=["Classificação epistemológica"])


class EpistemicClassInfo(BaseModel):
    id: EpistemicClass
    label: str
    required_metadata: list[str]
    allowed_in_astrology: bool


@router.get("/classes")
def list_classes() -> list[EpistemicClassInfo]:
    return [
        EpistemicClassInfo(
            id=cls,
            label=cls.label_pt,
            required_metadata=sorted(REQUIRED_METADATA[cls]),
            allowed_in_astrology=cls in ALLOWED_CLASSES[KnowledgeDomain.ASTROLOGY],
        )
        for cls in EpistemicClass
    ]
