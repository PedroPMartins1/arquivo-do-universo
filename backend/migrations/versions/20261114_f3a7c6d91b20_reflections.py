"""reflexões pessoais

Revision ID: f3a7c6d91b20
Revises: 2b57f59f1a01
Create Date: 2026-11-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3a7c6d91b20"
down_revision: str | Sequence[str] | None = "2b57f59f1a01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reflections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("slot", sa.SmallInteger(), nullable=True),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "slot IS NULL OR slot BETWEEN 0 AND 4",
            name=op.f("ck_reflections_slot_range"),
        ),
        sa.CheckConstraint(
            "char_length(body) BETWEEN 1 AND 5000",
            name=op.f("ck_reflections_body_length"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_reflections_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reflections")),
        sa.UniqueConstraint(
            "user_id",
            "day",
            "slot",
            name="uq_reflections_user_day_slot",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(op.f("ix_reflections_user_id"), "reflections", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reflections_user_id"), table_name="reflections")
    op.drop_table("reflections")
