from dataclasses import dataclass
import os


@dataclass(frozen=True)
class TelegramSettings:
    bot_token: str
    api_base_url: str
    mode: str = "polling"
    webhook_url: str | None = None
    mini_app_url: str | None = None
    request_timeout: float = 10.0

    @classmethod
    def from_env(cls) -> "TelegramSettings":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        api_base_url = os.getenv("CENTRAL_API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
        mode = os.getenv("TELEGRAM_MODE", "polling").strip().lower()
        webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL", "").strip() or None
        mini_app_url = os.getenv("TELEGRAM_MINI_APP_URL", "").strip() or None
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is required to start the Telegram bot")
        if mode not in {"polling", "webhook"}:
            raise ValueError("TELEGRAM_MODE must be polling or webhook")
        if mode == "webhook" and not webhook_url:
            raise ValueError("TELEGRAM_WEBHOOK_URL is required in webhook mode")
        return cls(bot_token=token, api_base_url=api_base_url, mode=mode, webhook_url=webhook_url, mini_app_url=mini_app_url)

    @property
    def telegram_api_url(self) -> str:
        return f"https://api.telegram.org/bot{self.bot_token}"
