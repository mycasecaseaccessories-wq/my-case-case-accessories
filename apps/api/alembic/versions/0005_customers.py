"""Add canonical customer identity foundation.

Revision ID: 0005_customers
Revises: 0004_users
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_customers"
down_revision = "0004_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("phone"),
    )
    op.create_index("ix_customers_email", "customers", ["email"])
    op.create_index("ix_customers_phone", "customers", ["phone"])
    op.add_column("orders", sa.Column("customer_id", sa.Uuid(), nullable=True))
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_foreign_key("fk_orders_customer_id", "orders", "customers", ["customer_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_orders_customer_id", "orders", type_="foreignkey")
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.drop_column("orders", "customer_id")
    op.drop_table("customers")
