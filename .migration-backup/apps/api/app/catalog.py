from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import require_roles
from .catalog_models import Category, Product
from .database import get_session

router = APIRouter(prefix="/catalog", tags=["catalog"])


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=140)
    description: str | None = None


class CategoryRead(CategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=140)
    description: str | None = None
    is_active: bool | None = None


class ProductCreate(BaseModel):
    category_id: UUID
    name: str = Field(min_length=1, max_length=180)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=200)
    sku: str = Field(min_length=1, max_length=80)
    description: str | None = None
    price: Decimal = Field(ge=0, decimal_places=2, max_digits=12)


class ProductRead(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    is_active: bool


class ProductUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=180)
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=200)
    sku: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    price: Decimal | None = Field(default=None, ge=0, decimal_places=2, max_digits=12)
    is_active: bool | None = None


@router.get("/categories", response_model=list[CategoryRead])
async def list_categories(session: AsyncSession = Depends(get_session)) -> list[Category]:
    result = await session.execute(select(Category).where(Category.is_active.is_(True)).order_by(Category.name))
    return list(result.scalars().all())


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, session: AsyncSession = Depends(get_session), _: object = Depends(require_roles("admin"))) -> Category:
    category = Category(**payload.model_dump())
    session.add(category)
    try:
        await session.commit()
        await session.refresh(category)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Category name or slug already exists") from exc
    return category


@router.patch("/categories/{category_id}", response_model=CategoryRead)
async def update_category(category_id: UUID, payload: CategoryUpdate, session: AsyncSession = Depends(get_session), _: object = Depends(require_roles("admin"))) -> Category:
    category = await session.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    try:
        await session.commit()
        await session.refresh(category)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Category name or slug already exists") from exc
    return category


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    category_id: UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> list[Product]:
    query = select(Product).where(Product.is_active.is_(True)).order_by(Product.name)
    if category_id is not None:
        query = query.where(Product.category_id == category_id)
    result = await session.execute(query)
    return list(result.scalars().all())


@router.get("/products/{product_id}", response_model=ProductRead)
async def get_product(product_id: UUID, session: AsyncSession = Depends(get_session)) -> Product:
    product = await session.get(Product, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/products/{product_id}", response_model=ProductRead)
async def update_product(product_id: UUID, payload: ProductUpdate, session: AsyncSession = Depends(get_session), _: object = Depends(require_roles("admin"))) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    changes = payload.model_dump(exclude_unset=True)
    if "category_id" in changes and not await session.get(Category, changes["category_id"]):
        raise HTTPException(status_code=400, detail="Category not found")
    for field, value in changes.items():
        setattr(product, field, value)
    try:
        await session.commit()
        await session.refresh(product)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Product slug or SKU already exists") from exc
    return product


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, session: AsyncSession = Depends(get_session), _: object = Depends(require_roles("admin"))) -> Product:
    if not await session.get(Category, payload.category_id):
        raise HTTPException(status_code=400, detail="Category not found")
    product = Product(**payload.model_dump())
    session.add(product)
    try:
        await session.commit()
        await session.refresh(product)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Product slug or SKU already exists") from exc
    return product
