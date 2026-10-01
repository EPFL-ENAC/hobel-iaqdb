"""download request

Revision ID: 5d1c0a7e9b21
Revises: a97d374f471c
Create Date: 2026-10-01 12:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5d1c0a7e9b21"
down_revision: Union[str, None] = "a97d374f471c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "download_request",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("query", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("n_records", sa.BigInteger(), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=True),
        sa.Column("s3_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("client_ip", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("ready_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("notified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_download_request_token_hash",
        "download_request",
        ["token_hash"],
        unique=True,
    )
    op.create_index("ix_download_request_email", "download_request", ["email"])
    op.create_index("ix_download_request_status", "download_request", ["status"])
    op.create_index("ix_download_request_client_ip", "download_request", ["client_ip"])


def downgrade() -> None:
    op.drop_table("download_request")
