import asyncio

from .bot import TelegramCommerceBot
from .commerce import CommerceApiClient
from .config import TelegramSettings
from .transport import TelegramApi, poll_forever
from .webhook import create_webhook_router


async def run() -> None:
    settings = TelegramSettings.from_env()
    commerce = CommerceApiClient(
        settings.api_base_url,
        timeout=settings.request_timeout,
        bot_token=settings.bot_token,
    )
    bot = TelegramCommerceBot(commerce, mini_app_url=settings.mini_app_url)
    telegram = TelegramApi(settings)
    if settings.mode == "webhook":
        assert settings.webhook_url is not None
        if not settings.webhook_secret_token:
            raise RuntimeError(
                "TELEGRAM_WEBHOOK_SECRET_TOKEN is required in webhook mode"
            )
        await telegram.set_webhook(settings.webhook_url, settings.webhook_secret_token)
        import uvicorn
        from fastapi import FastAPI

        app = FastAPI(title="My Case Telegram Webhook")
        app.include_router(
            create_webhook_router(bot, telegram, settings.webhook_secret_token)
        )
        config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
        await uvicorn.Server(config).serve()
        return
    await poll_forever(bot, telegram, asyncio.Event())


if __name__ == "__main__":
    asyncio.run(run())
