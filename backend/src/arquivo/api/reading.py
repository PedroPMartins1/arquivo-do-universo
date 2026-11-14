from datetime import date, datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from arquivo.api.deps import CurrentUser, Db, Now, get_text_model, has_immediate_access
from arquivo.api.profile import _chart, _daily_sky, _profile, _revelation_unlock_times
from arquivo.interpretation.model import InterpretationUnavailable, TextModel
from arquivo.interpretation.prompts import PROMPT_VERSION, SYSTEM
from arquivo.interpretation.service import (
    RevelationReading,
    day_prompt,
    interpret_day,
    interpret_natal,
    natal_prompt,
    prompt_hash,
)
from arquivo.persistence.accounts import audit
from arquivo.persistence.models import BirthProfile, Interpretation, User
from arquivo.transits.engine import DailySky

router = APIRouter(prefix="/me", tags=["Leituras"])
NOTE = (
    "Interpretação simbólica gerada por IA a partir do mapa calculado; não é ciência nem previsão."
)


class ReadingSection(BaseModel):
    id: str
    title: str
    text: str


class NatalReading(BaseModel):
    sections: list[ReadingSection]
    model: str
    prompt_version: str
    generated_at: datetime
    epistemic_class: Literal["interpretation"] = "interpretation"
    note: str = NOTE


class TodayReading(BaseModel):
    date: date
    theme: str | None
    revelations: list[RevelationReading | None]
    tomorrow: str | None
    model: str
    prompt_version: str
    generated_at: datetime
    epistemic_class: Literal["interpretation"] = "interpretation"
    note: str = NOTE


def _model_or_503(model: TextModel | None) -> TextModel:
    if model is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "a interpretação por IA ainda não está configurada",
        )
    return model


def _cached(
    db: Db, user: User, kind: str, day: date | None, facts_hash: str
) -> Interpretation | None:
    statement = select(Interpretation).where(
        Interpretation.user_id == user.id,
        Interpretation.kind == kind,
        Interpretation.facts_hash == facts_hash,
        Interpretation.day.is_(None) if day is None else Interpretation.day == day,
    )
    return db.scalar(statement)


def _store(
    db: Db,
    user: User,
    kind: str,
    day: date | None,
    facts_hash: str,
    model: TextModel,
    content: dict[str, Any],
    *,
    generated: bool,
    trigger: str,
) -> Interpretation:
    row = Interpretation(
        user_id=user.id,
        kind=kind,
        day=day,
        facts_hash=facts_hash,
        prompt_version=PROMPT_VERSION,
        model=model.name,
        content=content,
    )
    try:
        with db.begin_nested():
            db.add(row)
            db.flush()
    except IntegrityError:
        cached = _cached(db, user, kind, day, facts_hash)
        if cached is None:
            raise
        return cached
    if generated:
        audit(
            db,
            user.id,
            "interpretation.generated",
            kind=kind,
            model=model.name,
            trigger=trigger,
        )
    return row


def _natal_response(row: Interpretation) -> NatalReading:
    return NatalReading(
        sections=row.content["sections"],
        model=row.model,
        prompt_version=row.prompt_version,
        generated_at=row.created_at,
    )


def _today_response(row: Interpretation, sky: DailySky, now: datetime, user: User) -> TodayReading:
    unlocks = _revelation_unlock_times(sky)
    immediate = has_immediate_access(user)
    stored_revelations = row.content["revelations"]
    return TodayReading(
        date=sky.date,
        theme=row.content["theme"],
        revelations=[
            revelation if immediate or now >= unlocks_at else None
            for revelation, unlocks_at in zip(stored_revelations, unlocks, strict=True)
        ],
        tomorrow=row.content["tomorrow"],
        model=row.model,
        prompt_version=row.prompt_version,
        generated_at=row.created_at,
    )


@router.get("/reading/natal", response_model=NatalReading)
def natal_reading(
    user: CurrentUser,
    db: Db,
    model: Annotated[TextModel | None, Depends(get_text_model)],
) -> NatalReading:
    profile = _profile(db, user)
    model = _model_or_503(model)
    chart = _chart(profile)
    prompt, _ = natal_prompt(chart)
    facts_hash = prompt_hash(SYSTEM, prompt)
    cached = _cached(db, user, "natal", None, facts_hash)
    if cached is not None:
        return _natal_response(cached)
    try:
        sections = interpret_natal(chart, model)
    except InterpretationUnavailable as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "a interpretação não está disponível neste momento; tenta mais tarde",
        ) from error
    row = _store(
        db,
        user,
        "natal",
        None,
        facts_hash,
        model,
        {"sections": [section.__dict__ for section in sections]},
        generated=True,
        trigger="request",
    )
    return _natal_response(row)


@router.get("/reading/today", response_model=TodayReading)
def today_reading(
    user: CurrentUser,
    db: Db,
    model: Annotated[TextModel | None, Depends(get_text_model)],
    now: Now,
    day: Annotated[date | None, Query(alias="date")] = None,
) -> TodayReading:
    profile = _profile(db, user)
    model = _model_or_503(model)
    try:
        row, sky = ensure_day_reading(db, user, profile, model, now, day, trigger="request")
    except InterpretationUnavailable as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "a interpretação não está disponível neste momento; tenta mais tarde",
        ) from error
    return _today_response(row, sky, now, user)


def ensure_day_reading(
    db: Db,
    user: User,
    profile: BirthProfile,
    model: TextModel,
    now: datetime,
    day: date | None = None,
    *,
    trigger: str = "request",
) -> tuple[Interpretation, DailySky]:
    chart, sky = _daily_sky(user, profile, day, now=now)
    prompt, _ = day_prompt(sky, chart)
    facts_hash = prompt_hash(SYSTEM, prompt)
    cached = _cached(db, user, "day", sky.date, facts_hash)
    if cached is not None:
        return cached, sky
    reading = interpret_day(sky, chart, model)
    generated = bool(sky.revelations or sky.tomorrow)
    row = _store(
        db,
        user,
        "day",
        sky.date,
        facts_hash,
        model,
        {
            "theme": reading.theme,
            "revelations": [
                {
                    "title": revelation.title,
                    "text": revelation.text,
                    "question": revelation.question,
                }
                for revelation in reading.revelations
            ],
            "tomorrow": reading.tomorrow,
        },
        generated=generated,
        trigger=trigger,
    )
    return row, sky
