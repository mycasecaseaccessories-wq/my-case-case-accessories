from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import User, current_user
from .catalog_models import Product
from .database import get_session
from .orders import Order, OrderItem

router = APIRouter(prefix="/customer/orders", tags=["customer-orders"])


class CustomerOrderItemRead(BaseModel):
    product_id: UUID
    product_name: str
    sku: str
    quantity: int
    unit_price: Any


class CustomerOrderRead(BaseModel):
    id: UUID
    status: str
    total: Any
    created_at: Any
    items: list[CustomerOrderItemRead]


async def _customer_order_payload(session: AsyncSession, order: Order) -> dict[str, Any]:
    rows = await session.execute(
        select(OrderItem, Product)
        .join(Product, Product.id == OrderItem.product_id)
        .where(OrderItem.order_id == order.id)
    )
    return {
        "id": order.id,
        "status": order.status,
        "total": order.total,
        "created_at": order.created_at,
        "items": [
            {
                "product_id": item.product_id,
                "product_name": product.name,
                "sku": product.sku,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item, product in rows.all()
        ],
    }


async def _customer_id(user: User) -> UUID:
    if user.customer_id is None:
        raise HTTPException(status_code=409, detail="Customer account is not provisioned")
    return user.customer_id


@router.get("", response_model=list[CustomerOrderRead])
async def list_customer_orders(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    customer_id = await _customer_id(user)
    result = await session.execute(
        select(Order)
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return [await _customer_order_payload(session, order) for order in result.scalars().all()]


@router.get("/{order_id}", response_model=CustomerOrderRead)
async def get_customer_order(
    order_id: UUID,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    customer_id = await _customer_id(user)
    order = await session.scalar(select(Order).where(Order.id == order_id, Order.customer_id == customer_id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return await _customer_order_payload(session, order)
