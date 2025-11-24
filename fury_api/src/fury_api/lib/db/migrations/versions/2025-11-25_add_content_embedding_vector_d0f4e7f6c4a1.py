"""Add embedding vector to content for semantic search.

Revision ID: d0f4e7f6c4a1
Revises: 8116faf39023
Create Date: 2025-11-25 00:00:00.000000+00:00

"""

from __future__ import annotations

import warnings

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

# revision identifiers, used by Alembic.
revision = "d0f4e7f6c4a1"
down_revision = "8116faf39023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)

        schema_upgrades()
        data_upgrades()
        schema_upgrades_pos_data()


def downgrade() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)

        data_downgrades()
        schema_downgrades()


def schema_upgrades() -> None:
    """Schema upgrade migrations go here."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    with op.batch_alter_table("content", schema=None) as batch_op:
        batch_op.add_column(sa.Column("embedding", Vector(1536), nullable=True))

    op.create_index(
        op.f("ix_content_embedding"),
        "content",
        ["embedding"],
        unique=False,
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    op.drop_index(op.f("ix_content_embedding"), table_name="content")

    with op.batch_alter_table("content", schema=None) as batch_op:
        batch_op.drop_column("embedding")


def schema_upgrades_pos_data() -> None:
    """Schema upgrade migrations that need to be run after data migrations go here."""


def data_upgrades() -> None:
    """Data upgrade migrations go here."""


def data_downgrades() -> None:
    """Data downgrade migrations go here."""
