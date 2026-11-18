import argparse
import hashlib
import logging
import time as time_module
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import exists, func, select, tuple_

from arquivo.api.deps import get_text_model
from arquivo.api.reading import ensure_day_reading
from arquivo.config import Settings, get_settings
from arquivo.interpretation.model import TextModel
from arquivo.persistence.models import (
    AuthSession,
    BirthProfile,
    Interpretation,
    PregenerationFailure,
    User,
)
from arquivo.persistence.session import get_sessionmaker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PassReport:
    generated: int
    failed: int
    skipped_after_failures: int


class Pregenerator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def run_pass(self, now: datetime, model: TextModel) -> PassReport:
        sessionmaker = get_sessionmaker()
        with sessionmaker() as db:
            active_session = exists().where(
                AuthSession.user_id == User.id,
                AuthSession.expires_at > now,
            )
            candidates = db.execute(
                select(User.id, User.residence_zone, BirthProfile.zone)
                .join(BirthProfile, BirthProfile.user_id == User.id)
                .where(active_session)
            ).all()

            due: set[tuple[UUID, date]] = set()
            for user_id, residence_zone, birth_zone in candidates:
                local_now = now.astimezone(ZoneInfo(residence_zone or birth_zone))
                if local_now.time().replace(tzinfo=None) >= self.settings.pregeneration_start:
                    due.add((user_id, local_now.date()))

            if not due:
                return PassReport(0, 0, 0)

            existing = set(
                db.execute(
                    select(Interpretation.user_id, Interpretation.day).where(
                        Interpretation.kind == "day",
                        tuple_(Interpretation.user_id, Interpretation.day).in_(due),
                    )
                ).all()
            )

        generated = failed = skipped = 0
        with ThreadPoolExecutor(max_workers=self.settings.pregeneration_workers) as executor:
            futures = [
                executor.submit(self._generate, user_id, day, now, model)
                for user_id, day in sorted(due - existing)
            ]
            for future in as_completed(futures):
                outcome = future.result()
                generated += int(outcome == "generated")
                failed += int(outcome == "failed")
                skipped += int(outcome == "capped")

        return PassReport(generated, failed, skipped)

    def _generate(
        self, user_id: UUID, day: date, now: datetime, model: TextModel
    ) -> Literal["generated", "failed", "capped", "skipped"]:
        # O PostgreSQL liberta o bloqueio ao terminar a transação ou perder a ligação.
        digest = hashlib.blake2b(
            user_id.bytes + day.isoformat().encode(), digest_size=8, person=b"au-pregenerate"
        ).digest()
        lock_key = int.from_bytes(digest, "big", signed=True)
        with get_sessionmaker()() as session, session.begin():
            if not session.scalar(select(func.pg_try_advisory_xact_lock(lock_key))):
                return "skipped"
            already_generated = session.scalar(
                select(
                    exists().where(
                        Interpretation.user_id == user_id,
                        Interpretation.kind == "day",
                        Interpretation.day == day,
                    )
                )
            )
            if already_generated:
                return "skipped"
            failure = session.get(PregenerationFailure, (user_id, day))
            if failure is not None and failure.count >= self.settings.pregeneration_max_failures:
                return "capped"
            user = session.get(User, user_id)
            profile = session.get(BirthProfile, user_id)
            if user is None or profile is None:
                return "skipped"
            try:
                with session.begin_nested():
                    ensure_day_reading(
                        session, user, profile, model, now, day=day, trigger="pregeneration"
                    )
            except Exception as error:
                if failure is None:
                    session.add(PregenerationFailure(user_id=user_id, day=day, count=1))
                else:
                    failure.count += 1
                logger.warning(
                    "pré-geração falhou para utilizador %s: %s", user_id, type(error).__name__
                )
                return "failed"
        return "generated"


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    settings = get_settings()
    model = get_text_model()
    if model is None:
        logger.error("modelo de interpretação não configurado")
        return 2

    pregenerator = Pregenerator(settings)
    while True:
        try:
            report = pregenerator.run_pass(datetime.now(UTC), model)
        except Exception:
            logger.exception("passagem de pré-geração falhou")
            if args.once:
                return 1
            time_module.sleep(settings.pregeneration_interval_seconds)
            continue
        logger.info(
            "pré-geração: geradas=%d falhadas=%d ignoradas após falhas=%d",
            report.generated,
            report.failed,
            report.skipped_after_failures,
        )
        if args.once:
            return 0
        time_module.sleep(settings.pregeneration_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
