"""Consolidated documents/sources/conversations migration (platform schema).

Revision ID: 7485721da8b9
Revises: 567990e06e70
Create Date: 2025-11-17 15:31:44.814443+00:00
"""

from __future__ import annotations

import warnings

import sqlalchemy as sa
import sqlmodel
from alembic import op

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

# revision identifiers, used by Alembic.
revision = "7485721da8b9"
down_revision = "567990e06e70"
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

    # Grant permissions to tenant roles on new tables (following genesis pattern)
    op.execute(
        """
        do $$
        begin
            -- Grant permissions to tenant_user
            grant select, insert, update, delete on all tables in schema platform to tenant_user;
            grant usage on all sequences in schema platform to tenant_user;

            -- Grant read-only permissions to tenant_user_ro
            grant select on all tables in schema platform to tenant_user_ro;
            grant usage on all sequences in schema platform to tenant_user_ro;

            -- Set default privileges for future tables (if not already set)
            alter default privileges in schema platform grant select, insert, update, delete on tables to tenant_user;
            alter default privileges in schema platform grant usage on sequences to tenant_user;
            alter default privileges in schema platform grant select on tables to tenant_user_ro;
            alter default privileges in schema platform grant usage on sequences to tenant_user_ro;
        end;
        $$ language plpgsql;
        """
    )

    op.create_table(
        "document",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_document_organization_id_organization")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_document_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document")),
    )

    op.create_table(
        "source",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("source_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("handle", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("avatar_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("profile_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("platform_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("sync_status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("sync_error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("plugin_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_source_organization_id_organization")
        ),
        sa.ForeignKeyConstraint(["plugin_id"], ["plugin.id"], name=op.f("fk_source_plugin_id_plugin")),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_source_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source")),
        sa.UniqueConstraint("plugin_id", "external_id", "source_type", name="uq_source_plugin_external_type"),
    )

    op.create_table(
        "source_group",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("color", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("icon", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_source_group_organization_id_organization")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_source_group_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_group")),
    )

    op.create_table(
        "content",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("external_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("excerpt", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
        sa.Column("platform_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_content_organization_id_organization")
        ),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"], name=op.f("fk_content_source_id_source")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content")),
        sa.UniqueConstraint("source_id", "external_id", name="uq_content_source_external"),
    )

    op.create_table(
        "conversation",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"], name=op.f("fk_conversation_document_id_document")),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_conversation_organization_id_organization")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation")),
    )

    op.create_table(
        "document_content",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"], ["document.id"], name=op.f("fk_document_content_document_id_document")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_content")),
    )

    op.create_table(
        "document_source_config",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("source_group_id", sa.BigInteger(), nullable=True),
        sa.Column("source_id", sa.BigInteger(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(source_group_id IS NOT NULL) OR (source_id IS NOT NULL)",
            name=op.f("ck_document_source_config_ck_document_source_config_target"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["document.id"], name=op.f("fk_document_source_config_document_id_document")
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_document_source_config_organization_id_organization"),
        ),
        sa.ForeignKeyConstraint(
            ["source_group_id"],
            ["source_group.id"],
            name=op.f("fk_document_source_config_source_group_id_source_group"),
        ),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"], name=op.f("fk_document_source_config_source_id_source")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_source_config")),
        sa.UniqueConstraint("document_id", "source_group_id", name="uq_document_source_config_group"),
        sa.UniqueConstraint("document_id", "source_id", name="uq_document_source_config_source"),
    )

    op.create_table(
        "source_group_member",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("source_group_id", sa.BigInteger(), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organization.id"],
            name=op.f("fk_source_group_member_organization_id_organization"),
        ),
        sa.ForeignKeyConstraint(
            ["source_group_id"],
            ["source_group.id"],
            name=op.f("fk_source_group_member_source_group_id_source_group"),
        ),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"], name=op.f("fk_source_group_member_source_id_source")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_group_member")),
        sa.UniqueConstraint("source_group_id", "source_id", name="uq_source_group_member"),
    )

    op.create_table(
        "citation",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("document_id", sa.BigInteger(), nullable=False),
        sa.Column("content_id", sa.BigInteger(), nullable=False),
        sa.Column("citation_number", sa.Integer(), nullable=False),
        sa.Column("position_in_doc", sa.Integer(), nullable=True),
        sa.Column("section_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], name=op.f("fk_citation_content_id_content")),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"], name=op.f("fk_citation_document_id_document")),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_citation_organization_id_organization")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_citation")),
        sa.UniqueConstraint("document_id", "citation_number", name="uq_citation_document_number"),
    )

    op.create_table(
        "message",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("context_sources", sa.JSON(), nullable=True),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversation.id"], name=op.f("fk_message_conversation_id_conversation")
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_message_organization_id_organization")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_message")),
    )

    # RLS policies (following genesis pattern)
    op.execute(
        """
        do $$
        begin
            alter table document_source_config enable row level security;
            create policy tenant_policy on document_source_config to tenant_user
                using (organization_id = current_setting('app.current_organization_id')::bigint)
                with check (organization_id = current_setting('app.current_organization_id')::bigint);
            create policy tenant_policy_ro on document_source_config to tenant_user_ro
                using (organization_id = current_setting('app.current_organization_id')::bigint);
        end;
        $$ language plpgsql;
        """
    )

    op.execute(
        """
        do $$
        begin
            alter table source_group_member enable row level security;
            create policy tenant_policy on source_group_member to tenant_user
                using (organization_id = current_setting('app.current_organization_id')::bigint)
                with check (organization_id = current_setting('app.current_organization_id')::bigint);
            create policy tenant_policy_ro on source_group_member to tenant_user_ro
                using (organization_id = current_setting('app.current_organization_id')::bigint);
        end;
        $$ language plpgsql;
        """
    )

    op.execute(
        """
        do $$
        begin
            alter table citation enable row level security;
            create policy tenant_policy on citation to tenant_user
                using (organization_id = current_setting('app.current_organization_id')::bigint)
                with check (organization_id = current_setting('app.current_organization_id')::bigint);
            create policy tenant_policy_ro on citation to tenant_user_ro
                using (organization_id = current_setting('app.current_organization_id')::bigint);
        end;
        $$ language plpgsql;
        """
    )

    op.execute(
        """
        do $$
        begin
            alter table message enable row level security;
            create policy tenant_policy on message to tenant_user
                using (organization_id = current_setting('app.current_organization_id')::bigint)
                with check (organization_id = current_setting('app.current_organization_id')::bigint);
            create policy tenant_policy_ro on message to tenant_user_ro
                using (organization_id = current_setting('app.current_organization_id')::bigint);
        end;
        $$ language plpgsql;
        """
    )


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    op.execute("drop policy if exists tenant_policy_ro on message;")
    op.execute("drop policy if exists tenant_policy on message;")
    op.execute("alter table message disable row level security;")

    op.execute("drop policy if exists tenant_policy_ro on citation;")
    op.execute("drop policy if exists tenant_policy on citation;")
    op.execute("alter table citation disable row level security;")

    op.execute("drop policy if exists tenant_policy_ro on source_group_member;")
    op.execute("drop policy if exists tenant_policy on source_group_member;")
    op.execute("alter table source_group_member disable row level security;")

    op.execute("drop policy if exists tenant_policy_ro on document_source_config;")
    op.execute("drop policy if exists tenant_policy on document_source_config;")
    op.execute("alter table document_source_config disable row level security;")

    op.drop_table("message")
    op.drop_table("citation")
    op.drop_table("source_group_member")
    op.drop_table("document_source_config")
    op.drop_table("document_content")
    op.drop_table("conversation")
    op.drop_table("content")
    op.drop_table("source_group")
    op.drop_table("source")
    op.drop_table("document")


def schema_upgrades_pos_data() -> None:
    """Schema upgrade migrations that need to be run after data migrations go here."""


def data_upgrades() -> None:
    """Data upgrade migrations go here."""


def data_downgrades() -> None:
    """Data downgrade migrations go here."""
