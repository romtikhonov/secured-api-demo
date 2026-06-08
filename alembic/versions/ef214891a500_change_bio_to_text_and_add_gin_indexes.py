"""change bio to TEXT and add GIN indexes

Revision ID: ef214891a500
Revises: e575b2e7557c
Create Date: 2026-06-08 17:24:19.849705

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef214891a500"
down_revision: Union[str, Sequence[str], None] = "e575b2e7557c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "userprofile", "bio", existing_type=sa.VARCHAR(length=256), type_=sa.TEXT(), existing_nullable=False
    )

    op.execute("""
        CREATE INDEX ix_userprofile_bio_english_fts 
        ON userprofile 
        USING gin(to_tsvector('english', bio))
    """)
    op.execute("""
        CREATE INDEX ix_userprofile_bio_russian_fts 
        ON userprofile 
        USING gin(to_tsvector('russian', bio))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_userprofile_bio_russian_fts")
    op.execute("DROP INDEX IF EXISTS ix_userprofile_bio_english_fts")
    op.alter_column(
        "userprofile", "bio", existing_type=sa.TEXT(), type_=sa.VARCHAR(length=256), existing_nullable=False
    )
    # ### end Alembic commands ###
