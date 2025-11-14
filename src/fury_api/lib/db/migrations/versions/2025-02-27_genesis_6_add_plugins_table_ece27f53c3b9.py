"""Add plugins.

Revision ID: ece27f53c3b9
Revises: d0cbcbb4b236
Create Date: 2025-02-27 11:07:43.406518+00:00

"""

from __future__ import annotations

import warnings

import sqlalchemy as sa
from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

# revision identifiers, used by Alembic.
revision = "ece27f53c3b9"
down_revision = "d0cbcbb4b236"
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

    op.create_table(
        "plugin",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column(
            "organization_id", sa.BigInteger, sa.ForeignKey("organization.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("data_source", sa.String, nullable=False),
        sa.Column("credentials", sa.JSON, nullable=False),
        sa.Column("properties", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    # Enable Row-Level Security
    op.execute("ALTER TABLE plugin ENABLE ROW LEVEL SECURITY;")

    # Create an RLS policy based on organization_id
    op.execute(
        """
        CREATE POLICY org_based_rls ON plugin
        USING (
            organization_id = current_setting('app.current_organization_id')::BIGINT
            OR organization_id IS NULL
        );
        """
    )


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    op.execute("DROP POLICY IF EXISTS org_based_rls ON plugin;")
    op.execute("ALTER TABLE plugin DISABLE ROW LEVEL SECURITY;")
    op.drop_table("plugin")


def schema_upgrades_pos_data() -> None:
    """Schema upgrade migrations that need to be run after data migrations go here."""


def data_upgrades() -> None:
    """Data upgrade migrations go here."""


def data_downgrades() -> None:
    """Data downgrade migrations go here."""
