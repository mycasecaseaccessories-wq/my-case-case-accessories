from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx


@dataclass(frozen=True)
class TelegramProduct:
    id: str
    name: str
    price: Decimal
    sku: str


class CommerceApiClient:
    def __init__(self, api_base_url: str, timeout: float = 10.0) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout

    async def list_products(self) -> list[TelegramProduct]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.api_base_url}/catalog/products")
            response.raise_for_status()
            return [TelegramProduct(id=p["id"], name=p["name"], price=Decimal(str(p["price"])), sku=p["sku"]) for p in response.json()]

    async def create_order(self, customer_name: str, customer_phone: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.api_base_url}/orders", json={"customer_name": customer_name, "customer_phone": customer_phone, "items": items})
            response.raise_for_status()
            return response.json()


def format_product_menu(products: list[TelegramProduct]) -> str:
    if not products:
        return "လက်ရှိ product မရှိသေးပါ။"
    return "\n".join(f"{index}. {product.name} · {product.price:.2f} MMK · SKU {product.sku}" for index, product in enumerate(products, 1))
