from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Numeric, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from .catalog_models import Base, InventoryItem, Product
from .database import get_session

router = APIRouter(prefix="/orders", tags=["orders"])


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    customer_name: Mapped[str] = mapped_column(String(160))
    customer_phone: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="pending", server_default="pending")
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[int] = mapped_column()
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))


class OrderLine(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=999)


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=160)
    customer_phone: str = Field(min_length=5, max_length=40)
    items: list[OrderLine] = Field(min_length=1, max_length=50)


class OrderRead(BaseModel):
    id: UUID
    status: str
    total: Decimal


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderCreate, session: AsyncSession = Depends(get_session)) -> Order:
    order_total = Decimal("0")
    line_records: list[tuple[Product, InventoryItem, int]] = []
    for line in payload.items:
        product = await session.get(Product, line.product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=400, detail=f"Product not found: {line.product_id}")
        result = await session.execute(select(InventoryItem).where(InventoryItem.product_id == line.product_id).with_for_update())
        inventory = result.scalar_one_or_none()
        if inventory is None or inventory.quantity < line.quantity:
            raise HTTPException(status_code=409, detail=f"Insufficient stock: {product.name}")
        order_total += product.price * line.quantity
        line_records.append((product, inventory, line.quantity))
    order = Order(customer_name=payload.customer_name, customer_phone=payload.customer_phone, total=order_total)
    session.add(order)
    await session.flush()
    for product, inventory, quantity in line_records:
        inventory.quantity -= quantity
        session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=quantity, unit_price=product.price))
    await session.commit()
    await session.refresh(order)
    return order


@router.get("", response_model=list[OrderRead])
async def list_orders(session: AsyncSession = Depends(get_session)) -> list[Order]:
    result = await session.execute(select(Order).order_by(Order.created_at.desc()).limit(100))
    return list(result.scalars().all())


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: UUID, session: AsyncSession = Depends(get_session)) -> Order:
    order = await session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
