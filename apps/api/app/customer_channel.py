import json
import os
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import _validate_telegram_init_data
from .cart_models import Cart, CartItem
from .catalog_models import Product
from .customer_models import Customer
from .database import get_session
from .orders import Order, create_order_records
from .telegram_models import TelegramIdentity

router = APIRouter(prefix="/telegram", tags=["telegram-customer"])


class TelegramLinkRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=5, max_length=40)
    email: str | None = Field(default=None, max_length=255)


class CartLineRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0, le=999)


class CartItemRead(BaseModel):
    product_id: UUID
    product_name: str
    sku: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class CartRead(BaseModel):
    customer_id: UUID
    items: list[CartItemRead]
    total: Decimal


class CustomerOrderRead(BaseModel):
    id: UUID
    status: str
    total: Decimal
    created_at: Any


async def _telegram_user(
    init_data: str | None = Header(default=None, alias="X-Telegram-Init-Data"),
    bot_token: str | None = Header(default=None, alias="X-Telegram-Bot-Token"),
    bot_user_id: str | None = Header(default=None, alias="X-Telegram-User-Id"),
) -> tuple[str, str | None]:
    configured = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if init_data:
        if not configured:
            raise HTTPException(status_code=503, detail="Telegram authentication is not configured")
        try:
            pairs = _validate_telegram_init_data(init_data, configured)
            payload = json.loads(pairs.get("user", "{}"))
            telegram_id = str(payload.get("id", "")).strip()
            if not telegram_id:
                raise ValueError
            return telegram_id, payload.get("username")
        except (ValueError, TypeError, json.JSONDecodeError):
            raise HTTPException(status_code=401, detail="Invalid Telegram session")
    if bot_token and bot_user_id and configured and hmac_compare(bot_token, configured):
        if not bot_user_id.isdigit():
            raise HTTPException(status_code=401, detail="Invalid Telegram identity")
        return bot_user_id, None
    raise HTTPException(status_code=401, detail="Telegram authentication required")


def hmac_compare(left: str, right: str) -> bool:
    import hmac

    return hmac.compare_digest(left, right)


async def _identity_customer(
    identity: tuple[str, str | None] = Depends(_telegram_user), session: AsyncSession = Depends(get_session)
) -> tuple[TelegramIdentity, Customer]:
    telegram_id, username = identity
    record = await session.scalar(select(TelegramIdentity).where(TelegramIdentity.telegram_user_id == telegram_id))
    if record is None:
        raise HTTPException(status_code=409, detail="Telegram account is not linked to a customer")
    customer = await session.get(Customer, record.customer_id)
    if customer is None:
        raise HTTPException(status_code=409, detail="Telegram customer link is invalid")
    if username and record.username != username:
        record.username = username
        await session.commit()
    return record, customer


@router.post("/link", status_code=status.HTTP_200_OK)
async def link_telegram_customer(
    payload: TelegramLinkRequest,
    identity: tuple[str, str | None] = Depends(_telegram_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    telegram_id, username = identity
    existing = await session.scalar(select(TelegramIdentity).where(TelegramIdentity.telegram_user_id == telegram_id))
    matches = list(
        (await session.execute(select(Customer).where(Customer.phone == payload.phone.strip()))).scalars().all()
    )
    if existing:
        if not matches or matches[0].id != existing.customer_id:
            raise HTTPException(status_code=409, detail="Telegram account is already linked to another customer")
        return {"linked": True, "customer_id": str(existing.customer_id)}
    if len(matches) > 1:
        raise HTTPException(status_code=409, detail="Customer identity conflict")
    customer = (
        matches[0]
        if matches
        else Customer(
            full_name=payload.full_name.strip(),
            phone=payload.phone.strip(),
            email=payload.email.strip().lower() if payload.email else None,
        )
    )
    if matches and payload.email and customer.email and customer.email != payload.email.strip().lower():
        raise HTTPException(status_code=409, detail="Customer identity conflict")
    session.add(customer)
    await session.flush()
    record = TelegramIdentity(telegram_user_id=telegram_id, username=username, customer_id=customer.id)
    session.add(record)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Telegram identity or customer is already linked") from exc
    return {"linked": True, "customer_id": str(customer.id)}


async def _get_cart(session: AsyncSession, customer_id: UUID) -> Cart:
    cart = await session.scalar(select(Cart).where(Cart.customer_id == customer_id))
    if cart is None:
        cart = Cart(customer_id=customer_id)
        session.add(cart)
        await session.flush()
    return cart


async def _cart_read(session: AsyncSession, customer_id: UUID) -> CartRead:
    cart = await _get_cart(session, customer_id)
    rows = await session.execute(
        select(CartItem, Product).join(Product, Product.id == CartItem.product_id).where(CartItem.cart_id == cart.id)
    )
    items: list[CartItemRead] = []
    total = Decimal(0)
    for item, product in rows.all():
        if not product.is_active:
            continue
        line_total = product.price * item.quantity
        total += line_total
        items.append(
            CartItemRead(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                quantity=item.quantity,
                unit_price=product.price,
                line_total=line_total,
            )
        )
    return CartRead(customer_id=customer_id, items=items, total=total)


@router.get("/cart", response_model=CartRead)
async def read_cart(
    pair: tuple[TelegramIdentity, Customer] = Depends(_identity_customer), session: AsyncSession = Depends(get_session)
) -> CartRead:
    return await _cart_read(session, pair[1].id)


@router.post("/cart/items", response_model=CartRead)
async def upsert_cart_item(
    payload: CartLineRequest,
    pair: tuple[TelegramIdentity, Customer] = Depends(_identity_customer),
    session: AsyncSession = Depends(get_session),
) -> CartRead:
    product = await session.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product unavailable")
    cart = await _get_cart(session, pair[1].id)
    item = await session.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == payload.product_id).with_for_update()
    )
    if item is None:
        session.add(CartItem(cart_id=cart.id, product_id=payload.product_id, quantity=payload.quantity))
    else:
        item.quantity = payload.quantity
    await session.commit()
    return await _cart_read(session, pair[1].id)


@router.delete("/cart/items/{product_id}", response_model=CartRead)
async def delete_cart_item(
    product_id: UUID,
    pair: tuple[TelegramIdentity, Customer] = Depends(_identity_customer),
    session: AsyncSession = Depends(get_session),
) -> CartRead:
    cart = await _get_cart(session, pair[1].id)
    item = await session.scalar(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id).with_for_update()
    )
    if item is not None:
        await session.delete(item)
        await session.commit()
    return await _cart_read(session, pair[1].id)


@router.post("/cart/checkout", response_model=CustomerOrderRead, status_code=status.HTTP_201_CREATED)
async def checkout_cart(
    pair: tuple[TelegramIdentity, Customer] = Depends(_identity_customer), session: AsyncSession = Depends(get_session)
) -> Order:
    customer = pair[1]
    cart = await _get_cart(session, customer.id)
    rows = await session.execute(select(CartItem).where(CartItem.cart_id == cart.id).with_for_update())
    cart_items = list(rows.scalars().all())
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    order = await create_order_records(
        session,
        customer.id,
        customer.full_name,
        customer.phone or "",
        [(item.product_id, item.quantity) for item in cart_items],
    )
    for item in cart_items:
        await session.delete(item)
    await session.commit()
    await session.refresh(order)
    return order


@router.get("/orders", response_model=list[CustomerOrderRead])
async def customer_orders(
    pair: tuple[TelegramIdentity, Customer] = Depends(_identity_customer), session: AsyncSession = Depends(get_session)
) -> list[Order]:
    result = await session.execute(
        select(Order).where(Order.customer_id == pair[1].id).order_by(Order.created_at.desc()).limit(100)
    )
    return list(result.scalars().all())


@router.get("/orders/{order_id}", response_model=CustomerOrderRead)
async def customer_order(
    order_id: UUID,
    pair: tuple[TelegramIdentity, Customer] = Depends(_identity_customer),
    session: AsyncSession = Depends(get_session),
) -> Order:
    order = await session.scalar(select(Order).where(Order.id == order_id, Order.customer_id == pair[1].id))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
