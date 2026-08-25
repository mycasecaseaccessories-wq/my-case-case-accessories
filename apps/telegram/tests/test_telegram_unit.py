from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from apps.telegram.bot import TelegramCommerceBot
from apps.telegram.commerce import TelegramProduct, format_product_detail, format_product_menu
from apps.telegram.config import TelegramSettings


class FakeCommerce:
    def __init__(self) -> None:
        self.product_id = uuid4()
        self.products = [TelegramProduct(str(self.product_id), "Clear Case", Decimal(12000), "CC-001", "Slim case")]
        self.orders: list[dict[str, object]] = []

    async def list_categories(self):
        return [{"id": str(uuid4()), "name": "Cases"}]

    async def list_products(self, category_id=None):
        return self.products

    async def search_products(self, query):
        query = query.casefold()
        return [product for product in self.products if query in product.name.casefold() or query in product.sku.casefold()]

    async def get_product(self, product_id: UUID):
        assert product_id == self.product_id
        return self.products[0]

    async def find_or_create_customer(self, name, phone, email=None):
        return {"id": str(uuid4()), "name": name, "phone": phone}

    async def create_order(self, customer_id, customer_name, customer_phone, items):
        order = {"id": str(uuid4()), "status": "pending", "total": "12000.00"}
        self.orders.append(order)
        return order


@pytest.mark.asyncio
async def test_product_menu_and_detail_are_mmk_formatted():
    product = TelegramProduct("id", "Clear Case", Decimal(12000), "CC-001", "Slim case")
    assert "12000.00 MMK" in format_product_menu([product])
    assert "SKU: CC-001" in format_product_detail(product)


@pytest.mark.asyncio
async def test_bot_uses_central_customer_and_order_flow():
    fake = FakeCommerce()
    bot = TelegramCommerceBot(fake)  # type: ignore[arg-type]
    product_id = str(fake.product_id)
    assert "Clear Case" in await bot.handle_text(42, "/products")
    assert "Cases" in await bot.handle_text(42, "/categories")
    assert "ထည့်ပြီးပါပြီ" in await bot.handle_text(42, f"/add {product_id} 2")
    assert "ပြောင်းပြီးပါပြီ" in await bot.handle_text(42, f"/set {product_id} 3")
    assert "Clear Case" in await bot.handle_text(42, "/cart")
    confirmation = await bot.handle_text(42, "/checkout Mg Mg | 09999999999")
    assert "Order တင်ပြီးပါပြီ" in confirmation
    assert len(fake.orders) == 1
    await bot.handle_text(42, f"/add {product_id}")
    assert "ဖယ်ရှားပြီးပါပြီ" in await bot.handle_text(42, f"/remove {product_id}")


@pytest.mark.asyncio
async def test_unknown_or_unsupported_flow_is_safe():
    bot = TelegramCommerceBot(FakeCommerce(), mini_app_url="https://store.example")  # type: ignore[arg-type]
    assert bot.start_markup() is not None
    assert "store.example" in str(bot.start_markup())
    assert "မသိသော command" in await bot.handle_text(1, "/unknown")
    assert "TBD" in await bot.handle_text(1, f"/status {uuid4()}")


def test_telegram_settings_fail_closed_without_token(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        TelegramSettings.from_env()
