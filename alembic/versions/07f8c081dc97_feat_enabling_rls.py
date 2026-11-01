"""feat: enabling RLS

Revision ID: 07f8c081dc97
Revises: 24920534de6c
Create Date: 2026-10-30 21:26:56.262194

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "07f8c081dc97"
down_revision: Union[str, Sequence[str], None] = "24920534de6c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enabling RLS and creating policies to this"""

    op.execute('ALTER TABLE \"user\" ENABLE ROW LEVEL SECURITY')

    op.execute('DROP POLICY IF EXISTS select_user_policy ON \"user\"')
    op.execute('DROP POLICY IF EXISTS update_user_policy ON \"user\"')
    op.execute('DROP POLICY IF EXISTS delete_user_policy on \"user\"')

    op.execute("""
        CREATE POLICY select_user_policy ON \"user\"
        FOR SELECT
        USING (id = current_setting('app.current_id', true))
    """)
    op.execute("""
            CREATE POLICY update_user_policy ON \"user\"
            FOR UPDATE
            USING (id = current_setting('app.current_id', true))
            WITH CHECK (id = current_setting('app.current_id', true))
        """)
    op.execute("""
            CREATE POLICY delete_user_policy ON \"user\"
            FOR DELETE
            USING (id = current_setting('app.current_id', true))
        """)


def downgrade() -> None:
    """Disabling RLS and drop policies"""
    op.execute('DROP POLICY IF EXISTS select_user_policy ON \"user\"')
    op.execute('DROP POLICY IF EXISTS update_user_policy ON \"user\"')
    op.execute('DROP POLICY IF EXISTS delete_user_policy on \"user\"')

    op.execute('ALTER TABLE \"user\" DISABLE ROW LEVEL SECURITY')
