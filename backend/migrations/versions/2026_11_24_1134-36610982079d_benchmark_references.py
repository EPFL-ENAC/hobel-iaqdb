"""benchmark references

The benchmark table mirrors api/data/benchmarks.csv and the boot sync refills
it, so it is recreated rather than altered: the id becomes text
(docs/202-reference-values.md).

Revision ID: 36610982079d
Revises: b3d9e6f1a2c4
Create Date: 2026-11-24 11:34:09.198486

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "36610982079d"
down_revision: Union[str, None] = "b3d9e6f1a2c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("benchmark")
    op.create_table(
        "benchmark",
        sa.Column("id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("parameter", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("institution", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("region", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("limit_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("legal_status", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("setting", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("averaging", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("period", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("qualifier", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(["parameter"], ["parameter.slug"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("benchmark")
    op.create_table(
        "benchmark",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parameter", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("source", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("averaging", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(["parameter"], ["parameter.slug"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
