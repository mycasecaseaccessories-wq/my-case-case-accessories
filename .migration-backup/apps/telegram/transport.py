from typing import Any

import httpx

from .bot import TelegramCommerceBot
from .config import TelegramSettings


class TelegramApi:
    def __init__(self, settings: TelegramSettings) -> None:
        self.settings = settings

    async def call(self, method: str, **payload: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.settings.request_timeout) as client:
            response = await client.post(
                f"{self.settings.telegram_api_url}/{method}", json=payload
            )
            response.raise_for_status()
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError(
                    f"Telegram API error: {body.get('description', 'unknown error')}"
                )
            return body.get("result", {})

    async def send_message(
        self, chat_id: int, text: str, reply_markup: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return await self.call("sendMessage", **payload)

    async def get_updates(
        self, offset: int | None = None, timeout: int = 20
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout}
        if offset is not None:
            payload["offset"] = offset
        result: Any = await self.call("getUpdates", **payload)
        return list(result) if isinstance(result, list) else []

    async def set_webhook(
        self, url: str, secret_token: str | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"url": url}
        if secret_token:
            payload["secret_token"] = secret_token
        return await self.call("setWebhook", **payload)


async def dispatch_update(
    bot: TelegramCommerceBot, telegram_api: TelegramApi, update: dict[str, Any]
) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message or not message.get("text"):
        return
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None:
        return
    reply = await bot.handle_text(int(chat_id), str(message["text"]))
    markup = (
        bot.start_markup()
        if str(message["text"]).strip().casefold() == "/start"
        else None
    )
    await telegram_api.send_message(int(chat_id), reply, markup)


async def poll_forever(
    bot: TelegramCommerceBot, telegram_api: TelegramApi, stop_event: Any
) -> None:
    offset: int | None = None
    while not stop_event.is_set():
        updates = await telegram_api.get_updates(offset=offset)
        for update in updates:
            update_id = update.get("update_id")
            if isinstance(update_id, int):
                offset = update_id + 1
            await dispatch_update(bot, telegram_api, update)
