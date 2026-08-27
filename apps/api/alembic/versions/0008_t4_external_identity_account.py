"""generalize external identity links and associate authenticated users

Revision ID: 0008_t4_external_identity_account
Revises: 0007_external_identity_checkout_idempotency
"""
import sqlalchemy as sa

from alembic import op

revision = "0008_t4_external_identity_account"
down_revision = "0007_external_identity_checkout_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.rename_table("telegram_identities", "external_identities")
    op.alter_column("external_identities", "provider_user_id", new_column_name="provider_subject")
    op.drop_constraint("uq_external_identity_provider_user", "external_identities", type_="unique")
    op.create_unique_constraint(
        "uq_external_identity_provider_subject", "external_identities", ["provider", "provider_subject"]
    )
    op.add_column(
        "external_identities",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.add_column("external_identities", sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE external_identities SET created_at = linked_at WHERE created_at IS NULL")
    op.alter_column("external_identities", "created_at", nullable=False)
    op.drop_index("ix_telegram_identities_telegram_user_id", table_name="external_identities")
    op.create_index("ix_external_identities_provider_subject", "external_identities", ["provider_subject"])
    op.drop_index("ix_telegram_identities_customer_id", table_name="external_identities")
    op.create_index("ix_external_identities_customer_id", "external_identities", ["customer_id"])
    op.add_column("users", sa.Column("customer_id", sa.Uuid(), nullable=True))
    op.create_index("ix_users_customer_id", "users", ["customer_id"])
    op.create_foreign_key("fk_users_customer_id", "users", "customers", ["customer_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_users_customer_id", "users", type_="foreignkey")
    op.drop_index("ix_users_customer_id", table_name="users")
    op.drop_column("users", "customer_id")
    op.drop_index("ix_external_identities_customer_id", table_name="external_identities")
    op.create_index("ix_telegram_identities_customer_id", "external_identities", ["customer_id"])
    op.drop_index("ix_external_identities_provider_subject", table_name="external_identities")
    op.create_index("ix_telegram_identities_telegram_user_id", "external_identities", ["provider_subject"])
    op.alter_column("external_identities", "provider_subject", new_column_name="provider_user_id")
    op.drop_constraint("uq_external_identity_provider_subject", "external_identities", type_="unique")
    op.create_unique_constraint("uq_external_identity_provider_user", "external_identities", ["provider", "provider_user_id"])
    op.drop_column("external_identities", "last_verified_at")
    op.drop_column("external_identities", "created_at")
    op.rename_table("external_identities", "telegram_identities")
