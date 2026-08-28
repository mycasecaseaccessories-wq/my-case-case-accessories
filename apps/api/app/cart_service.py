from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from .cart_models import Cart, CartItem
from .catalog_models import Product


class CartService:
    """Central durable cart operations owned by a canonical Customer."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self, customer_id: UUID) -> Cart:
        cart = await self.session.scalar(select(Cart).where(Cart.customer_id == customer_id).with_for_update())
        if cart is None:
            cart = Cart(customer_id=customer_id)
            self.session.add(cart)
            await self.session.flush()
        return cart

    async def read(self, customer_id: UUID) -> dict[str, Any]:
        cart = await self.get_or_create(customer_id)
        rows = await self.session.execute(
            select(CartItem, Product)
            .join(Product, Product.id == CartItem.product_id)
            .where(CartItem.cart_id == cart.id)
        )
        items: list[dict[str, Any]] = []
        total = Decimal(0)
        for item, product in rows.all():
            if not product.is_active:
                continue
            line_total = product.price * item.quantity
            total += line_total
            items.append(
                {
                    "id": item.id,
                    "product_id": product.id,
                    "product_name": product.name,
                    "sku": product.sku,
                    "quantity": item.quantity,
                    "unit_price": product.price,
                    "line_total": line_total,
                }
            )
        return {
            "id": cart.id,
            "customer_id": customer_id,
            "items": items,
            "item_count": sum(i["quantity"] for i in items),
            "total": total,
        }

    async def add(self, customer_id: UUID, product_id: UUID, quantity: int) -> dict[str, Any]:
        if quantity <= 0 or quantity > 999:
            raise HTTPException(status_code=422, detail="Quantity must be between 1 and 999")
        product = await self.session.get(Product, product_id)
        if product is None or not product.is_active:
            raise HTTPException(status_code=404, detail="Product unavailable")
        cart = await self.get_or_create(customer_id)
        item = await self.session.scalar(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id).with_for_update()
        )
        if item is None:
            self.session.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity))
        else:
            item.quantity = min(999, item.quantity + quantity)
        await self.session.commit()
        return await self.read(customer_id)

    async def set_product(self, customer_id: UUID, product_id: UUID, quantity: int) -> dict[str, Any]:
        if quantity <= 0 or quantity > 999:
            raise HTTPException(status_code=422, detail="Quantity must be between 1 and 999")
        product = await self.session.get(Product, product_id)
        if product is None or not product.is_active:
            raise HTTPException(status_code=404, detail="Product unavailable")
        cart = await self.get_or_create(customer_id)
        item = await self.session.scalar(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id).with_for_update()
        )
        if item is None:
            self.session.add(CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity))
        else:
            item.quantity = quantity
        await self.session.commit()
        return await self.read(customer_id)

    async def remove_product(self, customer_id: UUID, product_id: UUID) -> dict[str, Any]:
        cart = await self.get_or_create(customer_id)
        item = await self.session.scalar(
            select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id).with_for_update()
        )
        if item is not None:
            await self.session.delete(item)
            await self.session.commit()
        return await self.read(customer_id)

    async def update(self, customer_id: UUID, item_id: UUID, quantity: int) -> dict[str, Any]:
        if quantity <= 0 or quantity > 999:
            raise HTTPException(status_code=422, detail="Quantity must be between 1 and 999")
        cart = await self.get_or_create(customer_id)
        item = await self.session.scalar(
            select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id).with_for_update()
        )
        if item is None:
            raise HTTPException(status_code=404, detail="Cart item not found")
        item.quantity = quantity
        await self.session.commit()
        return await self.read(customer_id)

    async def remove(self, customer_id: UUID, item_id: UUID) -> dict[str, Any]:
        cart = await self.get_or_create(customer_id)
        item = await self.session.scalar(
            select(CartItem).where(CartItem.id == item_id, CartItem.cart_id == cart.id).with_for_update()
        )
        if item is None:
            raise HTTPException(status_code=404, detail="Cart item not found")
        await self.session.delete(item)
        await self.session.commit()
        return await self.read(customer_id)

    async def clear(self, customer_id: UUID) -> dict[str, Any]:
        cart = await self.get_or_create(customer_id)
        await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        await self.session.commit()
        return await self.read(customer_id)
