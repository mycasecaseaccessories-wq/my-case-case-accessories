import asyncio

from .bot import TelegramCommerceBot
from .commerce import CommerceApiClient
from .config import TelegramSettings
from .transport import TelegramApi, poll_forever


async def run() -> None:
    settings = TelegramSettings.from_env()
    commerce = CommerceApiClient(settings.api_base_url, timeout=settings.request_timeout)
    bot = TelegramCommerceBot(commerce)
    telegram = TelegramApi(settings)
    if settings.mode == "webhook":
        assert settings.webhook_url is not None
        await telegram.set_webhook(settings.webhook_url)
        return
    await poll_forever(bot, telegram, asyncio.Event())


if __name__ == "__main__":
    asyncio.run(run())
