"""study drafts and files index, imported from S3

Revision ID: 8f4c2a9d7e13
Revises: 3e8f2b6c1d47
Create Date: 2026-10-14 12:00:00

"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8f4c2a9d7e13"
down_revision: Union[str, None] = "3e8f2b6c1d47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    study_draft = op.create_table(
        "study_draft",
        sa.Column("identifier", sa.String(), primary_key=True),
        sa.Column("document", postgresql.JSONB(), nullable=False),
    )
    study_file = op.create_table(
        "study_file",
        sa.Column("key", sa.String(), primary_key=True),
        sa.Column("study_identifier", sa.String(), nullable=False),
        sa.Column("area", sa.String(), nullable=False),
    )
    op.create_index(
        "ix_study_file_study_identifier", "study_file", ["study_identifier"]
    )

    # `alembic -x no_s3=1 upgrade head` skips the import (tests, CI)
    if context.is_offline_mode() or context.get_x_argument(as_dictionary=True).get(
        "no_s3"
    ):
        return
    from api.scripts.import_s3_drafts import read_s3

    # migrations run within the event loop of env.py: read S3 in another one
    with ThreadPoolExecutor(1) as executor:
        drafts, files = executor.submit(asyncio.run, read_s3()).result()
    op.bulk_insert(study_draft, drafts)
    op.bulk_insert(study_file, files)


def downgrade() -> None:
    # drafts edited since the upgrade are lost: S3 holds their former version
    op.drop_index("ix_study_file_study_identifier", table_name="study_file")
    op.drop_table("study_file")
    op.drop_table("study_draft")
