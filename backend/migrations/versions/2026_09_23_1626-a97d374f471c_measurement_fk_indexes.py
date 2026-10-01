"""measurement FK indexes

Every cascading foreign key of `measurement` gets an index on its column, so
deleting a building, instrument or study is an index lookup on the hypertable
instead of a full scan per deleted row (`space_id` and `dataset_id` already
lead an index).

Revision ID: a97d374f471c
Revises: ac49ec1ab264
Create Date: 2026-09-23 16:26:00

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a97d374f471c"
down_revision: Union[str, None] = "ac49ec1ab264"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_INDEXES = (
    ("ix_measurement_building_id", "building_id"),
    ("ix_measurement_instrument_id", "instrument_id"),
    ("ix_measurement_study_id", "study_id"),
)


def upgrade() -> None:
    for name, column in FK_INDEXES:
        op.create_index(name, "measurement", [column], unique=False, if_not_exists=True)


def downgrade() -> None:
    for name, _ in FK_INDEXES:
        op.drop_index(name, table_name="measurement")
