"""generalize external identity and add cart checkout idempotency

Revision ID: 0007_external_identity_checkout_idempotency
Revises: 0006_telegram_identity_and_carts
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_external_identity_checkout_idempotency"
down_revision = "0006_telegram_identity_and_carts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("telegram_identities", "telegram_user_id", new_column_name="provider_user_id")
    op.add_column(
        "telegram_identities", sa.Column("provider", sa.String(length=40), server_default="telegram", nullable=False)
    )
    op.create_unique_constraint(
        "uq_external_identity_provider_user", "telegram_identities", ["provider", "provider_user_id"]
    )
    op.add_column("carts", sa.Column("last_checkout_key", sa.String(length=128), nullable=True))
    op.add_column("carts", sa.Column("last_order_id", sa.Uuid(), nullable=True))
    op.create_unique_constraint("uq_carts_last_checkout_key", "carts", ["last_checkout_key"])
    op.create_foreign_key(
        "fk_carts_last_order_id_orders", "carts", "orders", ["last_order_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_carts_last_order_id_orders", "carts", type_="foreignkey")
    op.drop_constraint("uq_carts_last_checkout_key", "carts", type_="unique")
    op.drop_column("carts", "last_order_id")
    op.drop_column("carts", "last_checkout_key")
    op.drop_constraint("uq_external_identity_provider_user", "telegram_identities", type_="unique")
    op.drop_column("telegram_identities", "provider")
    op.alter_column("telegram_identities", "provider_user_id", new_column_name="telegram_user_id")
