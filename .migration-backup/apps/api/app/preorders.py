from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import User, current_user, require_roles
from .catalog_models import Product
from .customer_channel import _identity_customer
from .customer_models import Customer
from .database import get_session
from .orders import Order, OrderItem
from .preorder_models import PreOrder

router = APIRouter(prefix="/pre-orders", tags=["pre-orders"])
telegram_router = APIRouter(prefix="/telegram/pre-orders", tags=["telegram-pre-orders"])


class PreOrderCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=999)


class PreOrderStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=30)
    deposit_state: str | None = Field(default=None, min_length=1, max_length=30)


class PreOrderRead(BaseModel):
    id: UUID
    order_id: UUID
    order_item_id: UUID
    product_id: UUID
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    order_total: Decimal
    order_status: str
    status: str
    deposit_state: str
    created_at: Any
    updated_at: Any


async def _create_preorder(
    session: AsyncSession, customer: Customer, payload: PreOrderCreate, idempotency_key: str | None
) -> dict[str, Any]:
    if idempotency_key is not None:
        idempotency_key = idempotency_key.strip()
        if not idempotency_key or len(idempotency_key) > 128:
            raise HTTPException(status_code=400, detail="Invalid pre-order idempotency key")
        existing = await session.scalar(
            select(PreOrder).where(PreOrder.customer_id == customer.id, PreOrder.idempotency_key == idempotency_key)
        )
        if existing is not None:
            return await _preorder_payload(session, existing)
    product = await session.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product unavailable")
    if not product.pre_order_eligible:
        raise HTTPException(status_code=409, detail="Product is not eligible for pre-order")
    order = Order(
        customer_id=customer.id,
        customer_name=customer.full_name,
        customer_phone=customer.phone or "",
        status="pending",
        total=product.price * payload.quantity,
    )
    session.add(order)
    await session.flush()
    item = OrderItem(order_id=order.id, product_id=product.id, quantity=payload.quantity, unit_price=product.price)
    session.add(item)
    await session.flush()
    pre_order = PreOrder(
        order_id=order.id,
        order_item_id=item.id,
        customer_id=customer.id,
        idempotency_key=idempotency_key,
    )
    session.add(pre_order)
    await session.commit()
    await session.refresh(pre_order)
    return await _preorder_payload(session, pre_order)


async def _preorder_payload(session: AsyncSession, pre_order: PreOrder) -> dict[str, Any]:
    item = await session.get(OrderItem, pre_order.order_item_id)
    order = await session.get(Order, pre_order.order_id)
    if item is None or order is None:
        raise HTTPException(status_code=409, detail="Pre-order record is incomplete")
    product = await session.get(Product, item.product_id)
    if product is None:
        raise HTTPException(status_code=409, detail="Pre-order product is unavailable")
    return {
        "id": pre_order.id,
        "order_id": order.id,
        "order_item_id": item.id,
        "product_id": item.product_id,
        "product_name": product.name,
        "sku": product.sku,
        "quantity": item.quantity,
        "unit_price": item.unit_price,
        "order_total": order.total,
        "order_status": order.status,
        "status": pre_order.status,
        "deposit_state": pre_order.deposit_state,
        "created_at": pre_order.created_at,
        "updated_at": pre_order.updated_at,
    }


async def _user_customer(user: User, session: AsyncSession) -> Customer:
    if user.customer_id is None:
        raise HTTPException(status_code=409, detail="Customer account is not provisioned")
    customer = await session.get(Customer, user.customer_id)
    if customer is None:
        raise HTTPException(status_code=409, detail="Customer account is invalid")
    return customer


@router.post("", response_model=PreOrderRead, status_code=status.HTTP_201_CREATED)
async def create_preorder(
    payload: PreOrderCreate,
    idempotency_key: str | None = Header(default=None, alias="X-Preorder-Idempotency-Key"),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await _create_preorder(session, await _user_customer(user, session), payload, idempotency_key)


@router.get("", response_model=list[PreOrderRead])
async def list_preorders(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    customer = await _user_customer(user, session)
    result = await session.execute(
        select(PreOrder)
        .where(PreOrder.customer_id == customer.id)
        .order_by(PreOrder.created_at.desc(), PreOrder.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return [await _preorder_payload(session, row) for row in result.scalars().all()]


@router.get("/admin/list", response_model=list[PreOrderRead])
async def list_admin_preorders(
    limit: int = Query(default=100, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _: object = Depends(require_roles("admin")),
) -> list[dict[str, Any]]:
    result = await session.execute(select(PreOrder).order_by(PreOrder.created_at.desc()).limit(limit))
    return [await _preorder_payload(session, row) for row in result.scalars().all()]


@router.get("/{pre_order_id}", response_model=PreOrderRead)
async def get_preorder(
    pre_order_id: UUID, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    customer = await _user_customer(user, session)
    row = await session.scalar(select(PreOrder).where(PreOrder.id == pre_order_id, PreOrder.customer_id == customer.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Pre-order not found")
    return await _preorder_payload(session, row)


@router.patch("/{pre_order_id}", response_model=PreOrderRead)
async def update_preorder(
    pre_order_id: UUID,
    payload: PreOrderStatusUpdate,
    session: AsyncSession = Depends(get_session),
    _: object = Depends(require_roles("admin")),
) -> dict[str, Any]:
    row = await session.get(PreOrder, pre_order_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Pre-order not found")
    row.status = payload.status
    if payload.deposit_state is not None:
        row.deposit_state = payload.deposit_state
    await session.commit()
    return await _preorder_payload(session, row)


@telegram_router.post("", response_model=PreOrderRead, status_code=status.HTTP_201_CREATED)
async def create_telegram_preorder(
    payload: PreOrderCreate,
    idempotency_key: str | None = Header(default=None, alias="X-Preorder-Idempotency-Key"),
    pair: tuple[Any, Customer] = Depends(_identity_customer),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    return await _create_preorder(session, pair[1], payload, idempotency_key)
