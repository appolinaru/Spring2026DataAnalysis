"""add description to territories

Revision ID: c04dfea55d3c
Revises: 2d853c17f2cb
Create Date: 2026-06-11 15:24:14.216637

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c04dfea55d3c"
down_revision: Union[str, None] = "2d853c17f2cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "territories",
        sa.Column("description", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("territories", "description")
