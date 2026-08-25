from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .customer_models import Customer
from .database import get_session

router = APIRouter(prefix="/customers", tags=["customers"])


class CustomerCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=160)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=40)


class CustomerRead(CustomerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(payload: CustomerCreate, session: AsyncSession = Depends(get_session)) -> Customer:
    email = payload.email.strip().lower() if payload.email else None
    phone = payload.phone.strip() if payload.phone else None
    if not email and not phone:
        raise HTTPException(status_code=422, detail="Email or phone is required")
    identity_filters = [field == value for field, value in ((Customer.email, email), (Customer.phone, phone)) if value]
    duplicate = await session.scalar(select(Customer).where(or_(*identity_filters)))
    if duplicate:
        raise HTTPException(status_code=409, detail="A customer with this email or phone already exists")
    customer = Customer(full_name=payload.full_name.strip(), email=email, phone=phone)
    session.add(customer)
    try:
        await session.commit()
        await session.refresh(customer)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status_code=409, detail="Customer identity already exists") from exc
    return customer


@router.get("/lookup", response_model=list[CustomerRead])
async def lookup_customer(email: str | None = None, phone: str | None = None, session: AsyncSession = Depends(get_session)) -> list[Customer]:
    if not email and not phone:
        raise HTTPException(status_code=422, detail="Email or phone is required")
    query = select(Customer)
    if email:
        query = query.where(Customer.email == email.strip().lower())
    if phone:
        query = query.where(Customer.phone == phone.strip())
    result = await session.execute(query.limit(20))
    return list(result.scalars().all())


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(customer_id: UUID, session: AsyncSession = Depends(get_session)) -> Customer:
    customer = await session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
