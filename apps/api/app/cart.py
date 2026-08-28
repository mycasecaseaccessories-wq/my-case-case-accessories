from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import User, current_user
from .cart_service import CartService
from .database import get_session

router = APIRouter(prefix="/carts", tags=["carts"])


class CartItemRequest(BaseModel):
    product_id: UUID | None = None
    quantity: int = Field(gt=0, le=999)


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(gt=0, le=999)


async def _customer_id(user: User) -> UUID:
    if user.customer_id is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail="Customer account is not provisioned")
    return user.customer_id


@router.get("/current")
async def get_current_cart(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, object]:
    return await CartService(session).read(await _customer_id(user))


@router.post("/current/items")
async def add_current_cart_item(
    payload: CartItemRequest, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, object]:
    if payload.product_id is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="product_id is required")
    return await CartService(session).add(await _customer_id(user), payload.product_id, payload.quantity)


@router.patch("/current/items/{item_id}")
async def update_current_cart_item(
    item_id: UUID,
    payload: CartItemUpdateRequest,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return await CartService(session).update(await _customer_id(user), item_id, payload.quantity)


@router.delete("/current/items/{item_id}")
async def remove_current_cart_item(
    item_id: UUID, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, object]:
    return await CartService(session).remove(await _customer_id(user), item_id)


@router.delete("/current/items")
async def clear_current_cart(
    user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> dict[str, object]:
    return await CartService(session).clear(await _customer_id(user))
