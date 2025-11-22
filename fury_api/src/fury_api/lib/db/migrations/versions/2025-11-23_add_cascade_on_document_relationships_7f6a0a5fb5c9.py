"""Add cascade deletes for document and conversation relationships.

Revision ID: 7f6a0a5fb5c9
Revises: e8e179abf791
Create Date: 2025-11-23 00:00:00.000000+00:00
"""

from __future__ import annotations

import warnings

from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

# revision identifiers, used by Alembic.
revision = "7f6a0a5fb5c9"
down_revision = "e8e179abf791"
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

    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_conversation_document_id_document"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_conversation_document_id_document"),
            "document",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("document_content", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_document_content_document_id_document"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_document_content_document_id_document"),
            "document",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("document_source_config", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_document_source_config_document_id_document"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_document_source_config_document_id_document"),
            "document",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("citation", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_citation_document_id_document"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_citation_document_id_document"),
            "document",
            ["document_id"],
            ["id"],
            ondelete="CASCADE",
        )

    with op.batch_alter_table("message", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_message_conversation_id_conversation"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_message_conversation_id_conversation"),
            "conversation",
            ["conversation_id"],
            ["id"],
            ondelete="CASCADE",
        )


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""

    with op.batch_alter_table("message", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_message_conversation_id_conversation"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_message_conversation_id_conversation"), "conversation", ["conversation_id"], ["id"]
        )

    with op.batch_alter_table("citation", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_citation_document_id_document"), type_="foreignkey")
        batch_op.create_foreign_key(batch_op.f("fk_citation_document_id_document"), "document", ["document_id"], ["id"])

    with op.batch_alter_table("document_source_config", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_document_source_config_document_id_document"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_document_source_config_document_id_document"), "document", ["document_id"], ["id"]
        )

    with op.batch_alter_table("document_content", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_document_content_document_id_document"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_document_content_document_id_document"), "document", ["document_id"], ["id"]
        )

    with op.batch_alter_table("conversation", schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f("fk_conversation_document_id_document"), type_="foreignkey")
        batch_op.create_foreign_key(
            batch_op.f("fk_conversation_document_id_document"), "document", ["document_id"], ["id"]
        )


def schema_upgrades_pos_data() -> None:
    """Schema upgrade migrations that need to be run after data migrations go here."""


def data_upgrades() -> None:
    """Data upgrade migrations go here."""


def data_downgrades() -> None:
    """Data downgrade migrations go here."""
