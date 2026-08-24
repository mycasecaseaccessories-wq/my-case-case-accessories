import base64
import hashlib
import hmac
import json
import os
import time
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from .catalog_models import Base
from .database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])
_SECRET = os.getenv("JWT_SECRET", "change-me-in-production").encode()

class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="customer", server_default="customer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)

class UserRead(BaseModel):
    id: UUID
    email: str
    role: str

class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead

def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 180_000)
    return f"{base64.urlsafe_b64encode(salt).decode()}.{base64.urlsafe_b64encode(digest).decode()}"

def _verify_password(password: str, encoded: str) -> bool:
    try:
        salt_raw, digest_raw = encoded.split(".", 1)
        expected = _hash_password(password, base64.urlsafe_b64decode(salt_raw)).split(".", 1)[1]
        return hmac.compare_digest(expected, digest_raw)
    except (ValueError, TypeError):
        return False

def _make_token(user: User) -> str:
    payload = base64.urlsafe_b64encode(json.dumps({"sub": str(user.id), "role": user.role, "exp": int(time.time()) + 86400}, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def _decode_token(token: str) -> dict[str, object]:
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data["exp"]) < time.time():
            raise ValueError
        return data
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: Credentials, session: AsyncSession = Depends(get_session)) -> User:
    email = payload.email.strip().lower()
    if await session.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=email, password_hash=_hash_password(payload.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@router.post("/login", response_model=TokenRead)
async def login(payload: Credentials, session: AsyncSession = Depends(get_session)) -> TokenRead:
    user = await session.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if not user or not user.is_active or not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenRead(access_token=_make_token(user), user=user)

async def current_user(authorization: str | None = Header(default=None), session: AsyncSession = Depends(get_session)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    claims = _decode_token(authorization.split(" ", 1)[1])
    user = await session.get(User, UUID(str(claims["sub"])))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive or missing")
    return user

def require_roles(*roles: str):
    async def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency

@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(current_user)) -> User:
    return user
