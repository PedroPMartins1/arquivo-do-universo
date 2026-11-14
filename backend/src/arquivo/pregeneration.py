import argparse
import logging
import time as time_module
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import exists, select, tuple_

from arquivo.api.deps import get_text_model
from arquivo.api.reading import ensure_day_reading
from arquivo.config import Settings, get_settings
from arquivo.interpretation.model import TextModel
from arquivo.persistence.models import AuthSession, BirthProfile, Interpretation, User
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
        self.failures: dict[tuple[UUID, date], int] = {}

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

        jobs: list[tuple[UUID, date]] = []
        skipped = 0
        for candidate in sorted(due - existing):
            if self.failures.get(candidate, 0) >= self.settings.pregeneration_max_failures:
                skipped += 1
            else:
                jobs.append(candidate)

        generated = failed = 0
        with ThreadPoolExecutor(max_workers=self.settings.pregeneration_workers) as executor:
            futures = {
                executor.submit(self._generate, user_id, day, now, model): (user_id, day)
                for user_id, day in jobs
            }
            for future in as_completed(futures):
                candidate = futures[future]
                try:
                    succeeded = future.result()
                except Exception as error:
                    self.failures[candidate] = self.failures.get(candidate, 0) + 1
                    failed += 1
                    logger.warning(
                        "pré-geração falhou para utilizador %s: %s",
                        candidate[0],
                        type(error).__name__,
                    )
                else:
                    generated += int(succeeded)

        return PassReport(generated, failed, skipped)

    @staticmethod
    def _generate(user_id: UUID, day: date, now: datetime, model: TextModel) -> bool:
        with get_sessionmaker()() as session, session.begin():
            user = session.get(User, user_id)
            profile = session.get(BirthProfile, user_id)
            if user is None or profile is None:
                return False
            ensure_day_reading(
                session,
                user,
                profile,
                model,
                now,
                day=day,
                trigger="pregeneration",
            )
        return True


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
        report = pregenerator.run_pass(datetime.now(UTC), model)
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
