"""study-schema

Revision ID: 21b73f221ce8
Revises: 7c4f7731da01
Create Date: 2024-10-31 13:27:33.584737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '21b73f221ce8'
down_revision: Union[str, None] = '7c4f7731da01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('study', 'building_count')
    op.drop_column('study', 'space_count')


def downgrade() -> None:
    pass
