"""study_schema

Revision ID: 7b0ba8104864
Revises: 21b73f221ce8
Create Date: 2024-11-04 10:04:28.559967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7b0ba8104864'
down_revision: Union[str, None] = '21b73f221ce8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("building", sa.Column(
        "particle_filtration_rating", sa.Integer(), nullable=True))
    op.add_column("building", sa.Column(
        "age_group", sa.String(), nullable=True))
    op.add_column("building", sa.Column(
        "socioeconomic_status", sa.String(), nullable=True))
    op.drop_column("building", "special_population")

    op.add_column("space", sa.Column(
        "floor_area", sa.Float(), nullable=True))
    op.add_column("space", sa.Column(
        "space_volume", sa.Float(), nullable=True))
    op.add_column("space", sa.Column(
        "occupant_density", sa.Float(), nullable=True))
    op.drop_column("space", "particle_filtration_rating")


def downgrade() -> None:
    op.add_column("building", sa.Column(
        "special_population", sa.String(), nullable=True))
    op.drop_column("building", "particle_filtration_rating")
    op.drop_column("building", "age_group")
    op.drop_column("building", "socioeconomic_status")

    op.add_column("space", sa.Column(
        "particle_filtration_rating", sa.Integer(), nullable=True))
    op.drop_column("space", "floor_area")
    op.drop_column("space", "space_volume")
    op.drop_column("space", "occupant_density")
