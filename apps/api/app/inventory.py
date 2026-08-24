from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .catalog_models import InventoryItem, Product, StockMovement
from .database import get_session

router = APIRouter(prefix="/inventory", tags=["inventory"])


class InventoryRead(BaseModel):
    product_id: UUID
    quantity: int
    reorder_level: int
    low_stock: bool


class StockAdjustment(BaseModel):
    delta: int = Field(description="Positive for receiving stock, negative for deduction")
    reason: str = Field(min_length=1, max_length=120)


@router.get("", response_model=list[InventoryRead])
async def list_inventory(session: AsyncSession = Depends(get_session)) -> list[InventoryRead]:
    result = await session.execute(select(InventoryItem).join(Product).where(Product.is_active.is_(True)).order_by(InventoryItem.updated_at.desc()))
    return [InventoryRead(product_id=row.product_id, quantity=row.quantity, reorder_level=row.reorder_level, low_stock=row.quantity <= row.reorder_level) for row in result.scalars().all()]


@router.post("/{product_id}/adjust", response_model=InventoryRead)
async def adjust_stock(product_id: UUID, payload: StockAdjustment, session: AsyncSession = Depends(get_session)) -> InventoryRead:
    product = await session.get(Product, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    result = await session.execute(select(InventoryItem).where(InventoryItem.product_id == product_id).with_for_update())
    inventory = result.scalar_one_or_none()
    if inventory is None:
        inventory = InventoryItem(product_id=product_id, quantity=0, reorder_level=5)
        session.add(inventory)
        await session.flush()
    if inventory.quantity + payload.delta < 0:
        raise HTTPException(status_code=409, detail="Stock cannot become negative")
    inventory.quantity += payload.delta
    session.add(StockMovement(inventory_id=inventory.id, delta=payload.delta, reason=payload.reason))
    await session.commit()
    await session.refresh(inventory)
    return InventoryRead(product_id=inventory.product_id, quantity=inventory.quantity, reorder_level=inventory.reorder_level, low_stock=inventory.quantity <= inventory.reorder_level)
