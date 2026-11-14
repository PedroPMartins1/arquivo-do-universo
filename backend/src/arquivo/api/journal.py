from datetime import date, datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, StringConstraints, field_validator
from sqlalchemy import case, func, select, union
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from arquivo.api.deps import CurrentUser, Db, Now, has_immediate_access
from arquivo.api.profile import _daily_sky, _profile
from arquivo.api.reading import NOTE
from arquivo.config import get_settings
from arquivo.interpretation.prompts import SYSTEM
from arquivo.interpretation.service import RevelationReading, day_prompt, prompt_hash
from arquivo.persistence.accounts import audit
from arquivo.persistence.models import BirthProfile, Interpretation, Reflection, User
from arquivo.transits.engine import DailySky, Revelation
from arquivo.transits.unlock import unlock_times

router = APIRouter(prefix="/me", tags=["Diário e Arquivo"])


class ReflectionBody(BaseModel):
    body: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]

    @field_validator("body")
    @classmethod
    def reject_nul(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("o texto não pode conter caracteres NUL")
        return value


class ReflectionOut(BaseModel):
    day: date
    slot: int | None
    question: str | None
    body: str
    created_at: datetime
    updated_at: datetime
    provenance: Literal["user_reported"] = "user_reported"


class ArchiveDay(BaseModel):
    date: date
    theme: str | None
    revelation_count: int
    reflection_count: int
    has_note: bool


class ArchivePage(BaseModel):
    days: list[ArchiveDay]
    next_before: date | None


class ArchiveRevelation(BaseModel):
    unlocks_at: datetime
    reading: RevelationReading | None
    origin: Revelation | None


class ArchiveDayDetail(BaseModel):
    date: date
    theme: str | None
    revelations: list[ArchiveRevelation]
    reflections: list[ReflectionOut]
    model: str | None
    prompt_version: str | None
    generated_at: datetime | None
    epistemic_class: Literal["interpretation"] | None
    note: str | None


def _day_row(
    db: Session,
    user: User,
    day: date,
    facts_hash: str | None = None,
) -> Interpretation | None:
    statement = select(Interpretation).where(
        Interpretation.user_id == user.id,
        Interpretation.kind == "day",
        Interpretation.day == day,
    )
    if facts_hash is not None:
        matching = db.scalar(
            statement.where(Interpretation.facts_hash == facts_hash)
            .order_by(Interpretation.created_at.desc())
            .limit(1)
        )
        if matching is not None:
            return matching
    return db.scalar(
        statement
        .order_by(Interpretation.created_at.desc())
        .limit(1)
    )


def _current_day_facts(
    user: User,
    profile: BirthProfile,
    day: date,
    now: datetime,
) -> tuple[DailySky, str] | None:
    try:
        chart, sky = _daily_sky(user, profile, day, now=now)
        prompt, _ = day_prompt(sky, chart)
    except HTTPException:
        return None
    return sky, prompt_hash(SYSTEM, prompt)


def _zone(user: User, profile: BirthProfile) -> str:
    return user.residence_zone or profile.zone


def _local_today(user: User, profile: BirthProfile, now: datetime) -> date:
    return now.astimezone(ZoneInfo(_zone(user, profile))).date()


def _reject_future_day(user: User, profile: BirthProfile, day: date, now: datetime) -> None:
    if day > _local_today(user, profile, now):
        raise HTTPException(422, "não podes guardar reflexões para uma data futura")


def _stored_unlock_times(day: date, zone: str, count: int) -> list[datetime]:
    return unlock_times(day, ZoneInfo(zone), count, get_settings().revelation_unlock_times)


def _reflection_query(user: User, day: date, slot: int | None) -> Select[Reflection]:
    statement = select(Reflection).where(
        Reflection.user_id == user.id,
        Reflection.day == day,
        Reflection.slot.is_(None) if slot is None else Reflection.slot == slot,
    )
    return statement


def _reflection_out(row: Reflection) -> ReflectionOut:
    return ReflectionOut(
        day=row.day,
        slot=row.slot,
        question=row.question,
        body=row.body,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _upsert_reflection(
    db: Session,
    user: User,
    day: date,
    slot: int | None,
    question: str | None,
    body: str,
) -> ReflectionOut:
    statement = (
        pg_insert(Reflection)
        .values(user_id=user.id, day=day, slot=slot, question=question, body=body)
        .on_conflict_do_update(
            constraint="uq_reflections_user_day_slot",
            set_={"question": question, "body": body, "updated_at": func.now()},
        )
        .returning(Reflection)
        .execution_options(populate_existing=True)
    )
    row = db.scalar(statement)
    if row is None:
        raise RuntimeError("não foi possível guardar a reflexão")
    audit(db, user.id, "reflection.saved", day=day.isoformat(), slot=slot)
    return _reflection_out(row)


def _delete_reflection(db: Session, user: User, day: date, slot: int | None) -> Response:
    row = db.scalar(_reflection_query(user, day, slot))
    if row is not None:
        db.delete(row)
        audit(db, user.id, "reflection.deleted", day=day.isoformat(), slot=slot)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/reflections/{day}", response_model=list[ReflectionOut])
def get_reflections(day: date, user: CurrentUser, db: Db) -> list[ReflectionOut]:
    rows = db.scalars(
        select(Reflection)
        .where(Reflection.user_id == user.id, Reflection.day == day)
        .order_by(Reflection.slot.asc().nulls_last())
    ).all()
    return [_reflection_out(row) for row in rows]


@router.put("/reflections/{day}/note", response_model=ReflectionOut)
def save_note(
    day: date, data: ReflectionBody, user: CurrentUser, db: Db, now: Now
) -> ReflectionOut:
    profile = _profile(db, user)
    _reject_future_day(user, profile, day, now)
    return _upsert_reflection(db, user, day, None, None, data.body)


@router.delete("/reflections/{day}/note", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(day: date, user: CurrentUser, db: Db) -> Response:
    return _delete_reflection(db, user, day, None)


@router.put("/reflections/{day}/revelations/{slot}", response_model=ReflectionOut)
def save_revelation_reflection(
    day: date,
    slot: Annotated[int, Path(ge=0, le=4)],
    data: ReflectionBody,
    user: CurrentUser,
    db: Db,
    now: Now,
) -> ReflectionOut:
    profile = _profile(db, user)
    _reject_future_day(user, profile, day, now)
    row = _day_row(db, user, day)
    if row is None:
        raise HTTPException(404, "não existe uma leitura guardada para esse dia")
    current_facts = _current_day_facts(user, profile, day, now)
    if current_facts is not None:
        row = _day_row(db, user, day, current_facts[1]) or row
    revelations = row.content.get("revelations", [])
    if slot >= len(revelations):
        raise HTTPException(404, "não existe uma revelação nessa posição")
    existing = db.scalar(_reflection_query(user, day, slot))
    zone = _zone(user, profile)
    unlocks = _stored_unlock_times(day, zone, len(revelations))
    if existing is None and not has_immediate_access(user) and now < unlocks[slot]:
        raise HTTPException(409, "esta revelação ainda não abriu")
    return _upsert_reflection(
        db,
        user,
        day,
        slot,
        revelations[slot]["question"],
        data.body,
    )


@router.delete("/reflections/{day}/revelations/{slot}", status_code=status.HTTP_204_NO_CONTENT)
def delete_revelation_reflection(
    day: date,
    slot: Annotated[int, Path(ge=0, le=4)],
    user: CurrentUser,
    db: Db,
) -> Response:
    return _delete_reflection(db, user, day, slot)


@router.get("/archive", response_model=ArchivePage)
def get_archive(
    user: CurrentUser,
    db: Db,
    now: Now,
    before: date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> ArchivePage:
    profile = _profile(db, user)
    today = _local_today(user, profile, now)
    available_days = union(
        select(Interpretation.day.label("day")).where(
            Interpretation.user_id == user.id,
            Interpretation.kind == "day",
            Interpretation.day.is_not(None),
        ),
        select(Reflection.day.label("day")).where(Reflection.user_id == user.id),
    ).subquery()
    conditions = [available_days.c.day <= today]
    if before is not None:
        conditions.append(available_days.c.day < before)
    days = list(
        db.scalars(
            select(available_days.c.day)
            .where(*conditions)
            .order_by(available_days.c.day.desc())
            .limit(limit)
        ).all()
    )
    if not days:
        return ArchivePage(days=[], next_before=None)

    interpretation_rows = db.scalars(
        select(Interpretation)
        .where(
            Interpretation.user_id == user.id,
            Interpretation.kind == "day",
            Interpretation.day.in_(days),
        )
        .order_by(
            Interpretation.day.asc(),
            Interpretation.created_at.desc(),
            Interpretation.id.desc(),
        )
    ).all()
    latest: dict[date, Interpretation] = {}
    for row in interpretation_rows:
        if row.day is not None and row.day not in latest:
            latest[row.day] = row

    counts = db.execute(
        select(
            Reflection.day,
            func.count(Reflection.id),
            func.count(case((Reflection.slot.is_(None), 1))),
        )
        .where(Reflection.user_id == user.id, Reflection.day.in_(days))
        .group_by(Reflection.day)
    ).all()
    reflection_counts = {
        reflection_day: (int(count), int(notes) > 0) for reflection_day, count, notes in counts
    }
    summaries = []
    for day in days:
        stored = latest.get(day)
        count, has_note = reflection_counts.get(day, (0, False))
        revelations = stored.content.get("revelations", []) if stored is not None else []
        summaries.append(
            ArchiveDay(
                date=day,
                theme=stored.content.get("theme") if stored is not None else None,
                revelation_count=len(revelations),
                reflection_count=count,
                has_note=has_note,
            )
        )
    return ArchivePage(
        days=summaries,
        next_before=days[-1] if len(days) == limit else None,
    )


@router.get("/archive/{day}", response_model=ArchiveDayDetail)
def get_archive_day(day: date, user: CurrentUser, db: Db, now: Now) -> ArchiveDayDetail:
    profile = _profile(db, user)
    _reject_future_day(user, profile, day, now)
    row = _day_row(db, user, day)
    current_facts = (
        _current_day_facts(user, profile, day, now) if row is not None else None
    )
    if current_facts is not None:
        row = _day_row(db, user, day, current_facts[1]) or row
    reflection_rows = db.scalars(
        select(Reflection)
        .where(Reflection.user_id == user.id, Reflection.day == day)
        .order_by(Reflection.slot.asc().nulls_last())
    ).all()
    if row is None and not reflection_rows:
        raise HTTPException(404, "não há nada guardado para esse dia")

    zone = _zone(user, profile)
    stored_revelations = row.content.get("revelations", []) if row is not None else []
    unlocks = _stored_unlock_times(day, zone, len(stored_revelations))
    origins: list[Revelation | None] = [None] * len(stored_revelations)
    if row is not None and current_facts is not None:
        sky, current_hash = current_facts
        if row.facts_hash == current_hash and len(sky.revelations) == len(stored_revelations):
            origins = list(sky.revelations)

    immediate = has_immediate_access(user)
    revelations = []
    for index, content in enumerate(stored_revelations):
        is_open = immediate or now >= unlocks[index]
        revelations.append(
            ArchiveRevelation(
                unlocks_at=unlocks[index],
                reading=RevelationReading(**content) if is_open else None,
                origin=origins[index] if is_open else None,
            )
        )
    return ArchiveDayDetail(
        date=day,
        theme=row.content.get("theme") if row is not None else None,
        revelations=revelations,
        reflections=[_reflection_out(reflection) for reflection in reflection_rows],
        model=row.model if row is not None else None,
        prompt_version=row.prompt_version if row is not None else None,
        generated_at=row.created_at if row is not None else None,
        epistemic_class="interpretation" if row is not None else None,
        note=NOTE if row is not None else None,
    )
