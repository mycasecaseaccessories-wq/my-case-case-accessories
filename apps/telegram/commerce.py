from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx


@dataclass(frozen=True)
class TelegramProduct:
    id: str
    name: str
    price: Decimal
    sku: str
    description: str | None = None


class CommerceApiClient:
    """Thin adapter: all catalog, customer, stock and order truth stays in Central API."""

    def __init__(self, api_base_url: str, timeout: float = 10.0) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout = timeout

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, f"{self.api_base_url}{path}", **kwargs)
            response.raise_for_status()
            return response

    @staticmethod
    def _product(payload: dict[str, Any]) -> TelegramProduct:
        return TelegramProduct(
            id=str(payload["id"]),
            name=str(payload["name"]),
            price=Decimal(str(payload["price"])),
            sku=str(payload["sku"]),
            description=payload.get("description"),
        )

    async def list_products(self, category_id: UUID | None = None) -> list[TelegramProduct]:
        params = {"category_id": str(category_id)} if category_id else None
        response = await self._request("GET", "/catalog/products", params=params)
        return [self._product(item) for item in response.json()]

    async def search_products(self, query: str) -> list[TelegramProduct]:
        needle = query.strip().casefold()
        if not needle:
            return await self.list_products()
        products = await self.list_products()
        return [p for p in products if needle in p.name.casefold() or needle in p.sku.casefold()]

    async def get_product(self, product_id: UUID) -> TelegramProduct:
        response = await self._request("GET", f"/catalog/products/{product_id}")
        return self._product(response.json())

    async def find_or_create_customer(self, name: str, phone: str, email: str | None = None) -> dict[str, Any]:
        params: dict[str, str] = {"phone": phone.strip()}
        if email and email.strip():
            params["email"] = email.strip()
        lookup = await self._request("GET", "/customers/lookup", params=params)
        matches = lookup.json()
        if matches:
            return matches[0]
        payload: dict[str, str] = {"name": name.strip(), "phone": phone.strip()}
        if email and email.strip():
            payload["email"] = email.strip()
        response = await self._request("POST", "/customers", json=payload)
        return response.json()

    async def create_order(self, customer_id: UUID, customer_name: str, customer_phone: str, items: list[dict[str, Any]]) -> dict[str, Any]:
        response = await self._request(
            "POST",
            "/orders",
            json={
                "customer_id": str(customer_id),
                "customer_name": customer_name,
                "customer_phone": customer_phone,
                "items": items,
            },
        )
        return response.json()

    async def get_order_status(self, order_id: UUID, bearer_token: str | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {bearer_token}"} if bearer_token else None
        response = await self._request("GET", f"/orders/{order_id}", headers=headers)
        return response.json()


def format_product_menu(products: list[TelegramProduct]) -> str:
    if not products:
        return "လက်ရှိ product မရှိသေးပါ။"
    return "\n".join(
        f"{index}. {product.name} · {product.price:.2f} MMK · SKU {product.sku}"
        for index, product in enumerate(products, 1)
    )


def format_product_detail(product: TelegramProduct) -> str:
    description = f"\n{product.description}" if product.description else ""
    return f"{product.name}\nSKU: {product.sku}\nဈေးနှုန်း: {product.price:.2f} MMK{description}"
