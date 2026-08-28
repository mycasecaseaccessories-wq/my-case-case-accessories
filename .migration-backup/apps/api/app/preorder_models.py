from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .catalog_models import Base


class PreOrder(Base):
    """Pre-order specialization; Order and OrderItem remain sales authority."""

    __tablename__ = "pre_orders"
    __table_args__ = (UniqueConstraint("order_item_id", name="uq_pre_orders_order_item"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    order_item_id: Mapped[UUID] = mapped_column(ForeignKey("order_items.id", ondelete="CASCADE"), unique=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    status: Mapped[str] = mapped_column(String(30), default="requested", server_default="requested", index=True)
    deposit_state: Mapped[str] = mapped_column(String(30), default="not_required", server_default="not_required")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
