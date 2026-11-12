from fastapi import APIRouter
from pydantic import BaseModel

from arquivo import __version__
from arquivo.temporal.zones import TZDATA_VERSION

router = APIRouter(tags=["sistema"])


class Health(BaseModel):
    status: str
    version: str
    tzdata_version: str


@router.get("/health")
def health() -> Health:
    return Health(status="ok", version=__version__, tzdata_version=TZDATA_VERSION)
