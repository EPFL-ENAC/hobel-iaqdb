"""measurement_statistic

The `statistical` rows of the processed CSVs: summary statistics over a period,
kept apart from the readings of `measurement` (#174).

Revision ID: b3d9e6f1a2c4
Revises: 8f4c2a9d7e13
Create Date: 2026-10-28 12:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3d9e6f1a2c4"
down_revision: Union[str, None] = "8f4c2a9d7e13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES = (
    ("ix_measurement_statistic_parameter_start", ["parameter", "start_ts"]),
    ("ix_measurement_statistic_dataset_id", ["dataset_id"]),
    ("ix_measurement_statistic_study_id", ["study_id"]),
    ("ix_measurement_statistic_building_id", ["building_id"]),
    ("ix_measurement_statistic_space_id", ["space_id"]),
    ("ix_measurement_statistic_instrument_id", ["instrument_id"]),
)


def upgrade() -> None:
    op.create_table(
        "measurement_statistic",
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("study_id", sa.Integer(), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=True),
        sa.Column("space_id", sa.Integer(), nullable=True),
        sa.Column("instrument_id", sa.Integer(), nullable=True),
        sa.Column("parameter", sa.String(), nullable=False),
        sa.Column("statistic", sa.String(), nullable=False),
        sa.Column("start_ts", sa.TIMESTAMP(), nullable=False),
        sa.Column("end_ts", sa.TIMESTAMP(), nullable=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("value_qualifier", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["building_id"], ["building.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["dataset.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instrument.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["parameter"], ["parameter.slug"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["space_id"], ["space.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
    )
    for name, columns in INDEXES:
        op.create_index(name, "measurement_statistic", columns, unique=False)


def downgrade() -> None:
    op.drop_table("measurement_statistic")
