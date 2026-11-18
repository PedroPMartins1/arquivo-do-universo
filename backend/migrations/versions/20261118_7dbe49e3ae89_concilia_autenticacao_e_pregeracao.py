"""Concilia as migrações independentes da autenticação e da pré-geração."""

from collections.abc import Sequence

revision: str = "7dbe49e3ae89"
down_revision: tuple[str, str] = ("b8f2c0d91a47", "c0cc022174a6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Cada revisão anterior já cria a respetiva tabela.
    pass


def downgrade() -> None:
    pass
