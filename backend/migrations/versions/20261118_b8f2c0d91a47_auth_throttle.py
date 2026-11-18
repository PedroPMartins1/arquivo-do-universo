"""limites de autenticação partilhados

Revision ID: b8f2c0d91a47
Revises: f3a7c6d91b20
Create Date: 2026-11-18 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8f2c0d91a47"
down_revision: str | Sequence[str] | None = "f3a7c6d91b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_throttle",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_throttle")),
    )
    op.create_index(
        "ix_auth_throttle_scope_key_created",
        "auth_throttle",
        ["scope", "key_hash", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_auth_throttle_created_at",
        "auth_throttle",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_throttle_created_at", table_name="auth_throttle")
    op.drop_index("ix_auth_throttle_scope_key_created", table_name="auth_throttle")
    op.drop_table("auth_throttle")
