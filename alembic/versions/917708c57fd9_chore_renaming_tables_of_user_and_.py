"""chore renaming tables of "user" and "product"

Revision ID: 917708c57fd9
Revises: 7cc3bd6956c6
Create Date: 2026-10-30 23:03:55.114741

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '917708c57fd9'
down_revision: str | Sequence[str] | None = '7cc3bd6956c6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("product","products")
    op.rename_table("user","users")

def downgrade() -> None:
    """Downgrade schema."""

    op.rename_table("users","user")
    op.rename_table("products","product")
