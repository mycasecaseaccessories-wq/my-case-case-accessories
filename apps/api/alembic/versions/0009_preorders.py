"""add central-order-linked pre-orders and product eligibility

Revision ID: 0009_preorders
Revises: 0008_t4_external_identity_account
"""
import sqlalchemy as sa

from alembic import op

revision = "0009_preorders"
down_revision = "0008_t4_external_identity_account"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("pre_order_eligible", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.create_index("ix_products_pre_order_eligible", "products", ["pre_order_eligible"])
    op.create_table(
        "pre_orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("order_item_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="requested", nullable=False),
        sa.Column("deposit_state", sa.String(length=30), server_default="not_required", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_item_id", name="uq_pre_orders_order_item"),
        sa.UniqueConstraint("idempotency_key", name="uq_pre_orders_idempotency_key"),
    )
    op.create_index("ix_pre_orders_order_id", "pre_orders", ["order_id"])
    op.create_index("ix_pre_orders_customer_id", "pre_orders", ["customer_id"])
    op.create_index("ix_pre_orders_status", "pre_orders", ["status"])


def downgrade() -> None:
    op.drop_index("ix_pre_orders_status", table_name="pre_orders")
    op.drop_index("ix_pre_orders_customer_id", table_name="pre_orders")
    op.drop_index("ix_pre_orders_order_id", table_name="pre_orders")
    op.drop_table("pre_orders")
    op.drop_index("ix_products_pre_order_eligible", table_name="products")
    op.drop_column("products", "pre_order_eligible")
