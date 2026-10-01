"""dataset load times

Revision ID: 3e8f2b6c1d47
Revises: 5d1c0a7e9b21
Create Date: 2026-10-01 15:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3e8f2b6c1d47"
down_revision: Union[str, None] = "5d1c0a7e9b21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "dataset",
        sa.Column("load_started_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "dataset",
        sa.Column("load_finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("dataset", "load_finished_at")
    op.drop_column("dataset", "load_started_at")
