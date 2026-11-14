"""leituras interpretativas

Revision ID: 2b57f59f1a01
Revises: 65fffffc9b17
Create Date: 2026-11-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "2b57f59f1a01"
down_revision: str | Sequence[str] | None = "65fffffc9b17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interpretations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("day", sa.Date(), nullable=True),
        sa.Column("facts_hash", sa.CHAR(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("kind IN ('natal', 'day')", name=op.f("ck_interpretations_kind_values")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_interpretations_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interpretations")),
        sa.UniqueConstraint(
            "user_id",
            "kind",
            "day",
            "facts_hash",
            name="uq_interpretations_user_kind_day_facts_hash",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(
        op.f("ix_interpretations_user_id"), "interpretations", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_interpretations_user_id"), table_name="interpretations")
    op.drop_table("interpretations")
