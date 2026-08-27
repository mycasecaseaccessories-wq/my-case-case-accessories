from typing import Any

from fastapi import APIRouter, Header, HTTPException, status

from .bot import TelegramCommerceBot
from .transport import TelegramApi, dispatch_update


class UpdateDeduplicator:
    def __init__(self, max_size: int = 10_000) -> None:
        self._seen: set[int] = set()
        self._max_size = max_size

    def accept(self, update_id: object) -> bool:
        if not isinstance(update_id, int):
            return False
        if update_id in self._seen:
            return False
        if len(self._seen) >= self._max_size:
            self._seen.clear()
        self._seen.add(update_id)
        return True


def create_webhook_router(
    bot: TelegramCommerceBot, telegram_api: TelegramApi, secret_token: str
) -> APIRouter:
    router = APIRouter(prefix="/telegram", tags=["telegram-webhook"])
    deduplicator = UpdateDeduplicator()

    @router.post("/webhook", status_code=status.HTTP_204_NO_CONTENT)
    async def receive_webhook(
        update: dict[str, Any],
        x_telegram_bot_api_secret_token: str | None = Header(default=None),
    ) -> None:
        if not secret_token or x_telegram_bot_api_secret_token != secret_token:
            raise HTTPException(
                status_code=401, detail="Invalid Telegram webhook secret"
            )
        if not deduplicator.accept(update.get("update_id")):
            return
        await dispatch_update(bot, telegram_api, update)

    return router
