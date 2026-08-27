from typing import Protocol


class TelegramAdapter(Protocol):
    """Deferred adapter boundary; business truth remains in the Central Backend."""

    async def start(self) -> None:
        ...

    async def stop(self) -> None:
        ...
