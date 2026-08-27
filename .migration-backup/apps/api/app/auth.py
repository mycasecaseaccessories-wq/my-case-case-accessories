import base64
import hashlib
import hmac
import json
import os
import time
from urllib.parse import parse_qsl
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from .catalog_models import Base
from .config import settings
from .database import get_session

router = APIRouter(prefix="/auth", tags=["auth"])


def _secret() -> bytes:
    if not settings.jwt_secret and settings.app_env.lower() in {"production", "staging"}:
        raise RuntimeError("JWT_SECRET must be configured outside development")
    return (settings.jwt_secret or "development-only-secret").encode()

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


class TelegramInitData(BaseModel):
    init_data: str = Field(min_length=1, max_length=4096)


def _validate_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict[str, str]:
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", "")
    if not received_hash or not pairs:
        raise ValueError("Telegram init data is incomplete")
    data_check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, expected_hash):
        raise ValueError("Telegram init data signature is invalid")
    auth_date = int(pairs.get("auth_date", "0"))
    if auth_date <= 0 or time.time() - auth_date > max_age_seconds:
        raise ValueError("Telegram init data is expired")
    return pairs

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
    signature = hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"

def _decode_token(token: str) -> dict[str, object]:
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, hmac.new(_secret(), payload.encode(), hashlib.sha256).hexdigest()):
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
    return TokenRead(access_token=_make_token(user), user=UserRead.model_validate(user, from_attributes=True))

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

@router.post("/telegram/verify")
async def verify_telegram_init_data(payload: TelegramInitData) -> dict[str, object]:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not bot_token:
        raise HTTPException(status_code=503, detail="Telegram authentication is not configured")
    try:
        pairs = _validate_telegram_init_data(payload.init_data, bot_token)
        user_payload = json.loads(pairs.get("user", "{}"))
        return {"verified": True, "telegram_user_id": user_payload.get("id"), "username": user_payload.get("username")}
    except (ValueError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid Telegram session")


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(current_user)) -> User:
    return user
