"""IRREVERSABLE_convert_general_source_schema_to_author_collection_schema.

Revision ID: c134bcbc7280
Revises: d0f4e7f6c4a1
Create Date: 2025-11-27 23:37:13.364828+00:00

"""

from __future__ import annotations

import warnings

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

__all__ = ["downgrade", "upgrade", "schema_upgrades", "schema_downgrades", "data_upgrades", "data_downgrades"]

# revision identifiers, used by Alembic.
revision = "c134bcbc7280"
down_revision = "d0f4e7f6c4a1"
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
        "author",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("platform", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("handle", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("avatar_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("profile_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("bio", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("follower_count", sa.Integer(), nullable=True),
        sa.Column("following_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_author")),
        sa.UniqueConstraint("platform", "external_id", name="uq_author_platform_external"),
    )
    op.create_table(
        "collection",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("platform", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("collection_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("plugin_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["platform.organization.id"], name=op.f("fk_collection_organization_id_organization")
        ),
        sa.ForeignKeyConstraint(["plugin_id"], ["platform.plugin.id"], name=op.f("fk_collection_plugin_id_plugin")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collection")),
        sa.UniqueConstraint("organization_id", "platform", "name", name="uq_collection_platform_name"),
    )
    op.create_table(
        "content_collection",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BigInteger(), nullable=False),
        sa.Column("content_id", sa.BigInteger(), nullable=False),
        sa.Column("collection_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["collection_id"], ["platform.collection.id"], name=op.f("fk_content_collection_collection_id_collection")
        ),
        sa.ForeignKeyConstraint(
            ["content_id"], ["platform.content.id"], name=op.f("fk_content_collection_content_id_content")
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["platform.organization.id"],
            name=op.f("fk_content_collection_organization_id_organization"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_collection")),
        sa.UniqueConstraint("organization_id", "content_id", "collection_id", name="uq_content_collection"),
    )

    # Remove RLS on content before dropping organization_id
    op.execute(
        """
        do $$
        begin
            drop policy if exists tenant_policy on content;
            drop policy if exists tenant_policy_ro on content;
            alter table if exists content disable row level security;
        end;
        $$ language plpgsql;
        """
    )

    with op.batch_alter_table("content", schema=None) as batch_op:
        batch_op.add_column(sa.Column("author_id", sa.BigInteger(), nullable=True))
        batch_op.drop_index(
            batch_op.f("ix_content_embedding"),
            postgresql_ops={"embedding": "vector_cosine_ops"},
            postgresql_with={"lists": "100"},
            postgresql_using="ivfflat",
        )
        batch_op.drop_constraint(batch_op.f("uq_content_source_external"), type_="unique")
        batch_op.create_unique_constraint("uq_content_external_id", ["external_id"])
        batch_op.drop_constraint(batch_op.f("fk_content_organization_id_organization"), type_="foreignkey")
        batch_op.drop_constraint(batch_op.f("fk_content_source_id_source"), type_="foreignkey")
        batch_op.create_foreign_key(batch_op.f("fk_content_author_id_author"), "author", ["author_id"], ["id"])
        batch_op.drop_column("source_id")
        batch_op.drop_column("organization_id")

    # Drop in dependency order to avoid FK issues
    op.drop_table("document_source_config")
    op.drop_table("source_group_member")
    op.drop_table("citation")
    op.drop_table("source")
    op.drop_table("source_group")

    op.execute("""
        do $$
        begin
            alter table "collection" enable row level security;

            create policy tenant_policy on "collection" to tenant_user
                using (organization_id = current_setting(\'app.current_organization_id\')::bigint);

            create policy tenant_policy_ro on "collection" to tenant_user_ro
                using (organization_id = current_setting(\'app.current_organization_id\')::bigint);

        end;
        $$ language plpgsql;
       """)
    op.execute("""
        do $$
        begin
            alter table "content_collection" enable row level security;

            create policy tenant_policy on "content_collection" to tenant_user
                using (organization_id = current_setting(\'app.current_organization_id\')::bigint);

            create policy tenant_policy_ro on "content_collection" to tenant_user_ro
                using (organization_id = current_setting(\'app.current_organization_id\')::bigint);

        end;
        $$ language plpgsql;
       """)


def schema_downgrades() -> None:
    """Schema downgrade migrations go here."""
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("content", schema=None) as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.BIGINT(), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column("source_id", sa.BIGINT(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(batch_op.f("fk_content_author_id_author"), type_="foreignkey")
        batch_op.create_foreign_key(batch_op.f("fk_content_source_id_source"), "source", ["source_id"], ["id"])
        batch_op.create_foreign_key(
            batch_op.f("fk_content_organization_id_organization"), "organization", ["organization_id"], ["id"]
        )
        batch_op.drop_constraint("uq_content_external_id", type_="unique")
        batch_op.create_unique_constraint(
            batch_op.f("uq_content_source_external"), ["source_id", "external_id"], postgresql_nulls_not_distinct=False
        )
        batch_op.create_index(
            batch_op.f("ix_content_embedding"),
            ["embedding"],
            unique=False,
            postgresql_ops={"embedding": "vector_cosine_ops"},
            postgresql_with={"lists": "100"},
            postgresql_using="ivfflat",
        )
        batch_op.drop_column("author_id")

    op.create_table(
        "source",
        sa.Column(
            "id",
            sa.BIGINT(),
            server_default=sa.text("nextval('source_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("organization_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("source_type", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("external_id", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("display_name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("handle", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("avatar_url", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("profile_url", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("platform_type", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("is_active", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("last_synced_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
        sa.Column("sync_status", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("sync_error", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("plugin_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("user_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.Column("updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name="fk_source_organization_id_organization"
        ),
        sa.ForeignKeyConstraint(["plugin_id"], ["plugin.id"], name="fk_source_plugin_id_plugin"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name="fk_source_user_id_user"),
        sa.PrimaryKeyConstraint("id", name="pk_source"),
        sa.UniqueConstraint(
            "plugin_id",
            "external_id",
            "source_type",
            name="uq_source_plugin_external_type",
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
        postgresql_ignore_search_path=False,
    )
    op.create_table(
        "document_source_config",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("document_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("source_group_id", sa.BIGINT(), autoincrement=False, nullable=True),
        sa.Column("source_id", sa.BIGINT(), autoincrement=False, nullable=True),
        sa.Column("enabled", sa.BOOLEAN(), autoincrement=False, nullable=False),
        sa.Column("added_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.CheckConstraint(
            "source_group_id IS NOT NULL OR source_id IS NOT NULL",
            name=op.f("ck_document_source_config_ck_document_source_config_target"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
            name=op.f("fk_document_source_config_document_id_document"),
            ondelete="CASCADE",
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
        sa.UniqueConstraint(
            "document_id",
            "source_group_id",
            name=op.f("uq_document_source_config_group"),
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
        sa.UniqueConstraint(
            "document_id",
            "source_id",
            name=op.f("uq_document_source_config_source"),
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
    )
    op.create_table(
        "source_group_member",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("source_group_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("source_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("added_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_source_group_member_organization_id_organization")
        ),
        sa.ForeignKeyConstraint(
            ["source_group_id"], ["source_group.id"], name=op.f("fk_source_group_member_source_group_id_source_group")
        ),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"], name=op.f("fk_source_group_member_source_id_source")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_group_member")),
        sa.UniqueConstraint(
            "source_group_id",
            "source_id",
            name=op.f("uq_source_group_member"),
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
    )
    op.create_table(
        "citation",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("document_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("content_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("citation_number", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("position_in_doc", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("section_index", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["content.id"], name=op.f("fk_citation_content_id_content")),
        sa.ForeignKeyConstraint(
            ["document_id"], ["document.id"], name=op.f("fk_citation_document_id_document"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_citation_organization_id_organization")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_citation")),
        sa.UniqueConstraint(
            "document_id",
            "citation_number",
            name=op.f("uq_citation_document_number"),
            postgresql_include=[],
            postgresql_nulls_not_distinct=False,
        ),
    )
    op.create_table(
        "source_group",
        sa.Column("id", sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("color", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("icon", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("user_id", sa.BIGINT(), autoincrement=False, nullable=False),
        sa.Column("created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], name=op.f("fk_source_group_organization_id_organization")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], name=op.f("fk_source_group_user_id_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_group")),
    )
    op.drop_table("content_collection")
    op.drop_table("collection")
    op.drop_table("author")
    # ### end Alembic commands ###


def schema_upgrades_pos_data() -> None:
    """Schema upgrade migrations that need to be run after data migrations go here."""


def data_upgrades() -> None:
    """Data upgrade migrations go here."""


def data_downgrades() -> None:
    """Data downgrade migrations go here."""
