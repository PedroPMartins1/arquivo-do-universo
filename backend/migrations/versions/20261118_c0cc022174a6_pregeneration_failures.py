"""Contagem partilhada de falhas de pré-geração por utilizador e dia local."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c0cc022174a6"
down_revision: str | Sequence[str] | None = "f3a7c6d91b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pregeneration_failures",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.CheckConstraint("count > 0", name=op.f("ck_pregeneration_failures_positive_count")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_pregeneration_failures_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "day", name=op.f("pk_pregeneration_failures")),
    )


def downgrade() -> None:
    op.drop_table("pregeneration_failures")
