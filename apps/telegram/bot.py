from dataclasses import dataclass, field
from uuid import UUID

import httpx

from .commerce import CommerceApiClient, format_product_detail, format_product_menu


@dataclass
class CartLine:
    product_id: UUID
    quantity: int = 1


@dataclass
class TelegramCommerceBot:
    api: CommerceApiClient
    carts: dict[int, dict[UUID, CartLine]] = field(default_factory=dict)

    def _cart(self, chat_id: int) -> dict[UUID, CartLine]:
        return self.carts.setdefault(chat_id, {})

    async def handle_text(self, chat_id: int, text: str) -> str:
        try:
            command, _, argument = text.strip().partition(" ")
            command = command.casefold()
            if command in {"/start", "/help"}:
                return (
                    "My Case သို့ ကြိုဆိုပါတယ်။\n"
                    "/products - Product စာရင်း\n"
                    "/search <စကားလုံး> - ရှာရန်\n"
                    "/product <id> - အသေးစိတ်\n"
                    "/add <id> [အရေအတွက်] - Cart ထဲထည့်ရန်\n"
                    "/cart - Cart ကြည့်ရန်\n"
                    "/checkout <အမည်> | <ဖုန်း> - Order တင်ရန်\n"
                    "/status <order-id> - Order status"
                )
            if command == "/products":
                return format_product_menu(await self.api.list_products())
            if command == "/search":
                if not argument.strip():
                    return "ရှာဖွေရန် စကားလုံး ထည့်ပေးပါ။ ဥပမာ /search case"
                return format_product_menu(await self.api.search_products(argument))
            if command == "/product":
                product_id = UUID(argument.strip())
                return format_product_detail(await self.api.get_product(product_id))
            if command == "/add":
                parts = argument.split()
                if not parts:
                    return "Product ID ထည့်ပေးပါ။ ဥပမာ /add <product-id> 1"
                product_id = UUID(parts[0])
                quantity = int(parts[1]) if len(parts) > 1 else 1
                if quantity < 1 or quantity > 999:
                    return "အရေအတွက်သည် 1 မှ 999 အတွင်း ဖြစ်ရပါမည်။"
                self._cart(chat_id)[product_id] = CartLine(product_id, quantity)
                return "Cart ထဲသို့ ထည့်ပြီးပါပြီ။ /cart ဖြင့် စစ်ဆေးနိုင်ပါတယ်။"
            if command == "/cart":
                cart = self._cart(chat_id)
                if not cart:
                    return "Cart လွတ်နေပါတယ်။ /products ဖြင့် စတင်ရွေးချယ်ပါ။"
                lines = []
                for index, line in enumerate(cart.values(), 1):
                    product = await self.api.get_product(line.product_id)
                    lines.append(f"{index}. {product.name} × {line.quantity} = {product.price * line.quantity:.2f} MMK")
                return "\n".join(lines) + "\n\nOrder တင်ရန် /checkout အမည် | ဖုန်း"
            if command == "/checkout":
                parts = [part.strip() for part in argument.split("|")]
                if len(parts) != 2 or not all(parts):
                    return "Format: /checkout အမည် | ဖုန်း"
                cart = self._cart(chat_id)
                if not cart:
                    return "Cart လွတ်နေပါတယ်။"
                customer = await self.api.find_or_create_customer(parts[0], parts[1])
                customer_id = UUID(str(customer["id"]))
                order = await self.api.create_order(
                    customer_id,
                    parts[0],
                    parts[1],
                    [{"product_id": str(line.product_id), "quantity": line.quantity} for line in cart.values()],
                )
                cart.clear()
                return f"Order တင်ပြီးပါပြီ။ Order ID: {order['id']}\nStatus: {order['status']}\nစုစုပေါင်း: {order['total']} MMK"
            if command == "/status":
                if not argument.strip():
                    return "Order ID ထည့်ပေးပါ။"
                # Current central endpoint is admin-protected. Do not bypass ownership rules.
                return "Order status lookup သည် customer ownership API မသတ်မှတ်ရသေးသဖြင့် ယာယီ TBD ဖြစ်ပါတယ်။"
            return "မသိသော command ဖြစ်ပါတယ်။ /help ဖြင့် အသုံးပြုနိုင်သော command များကို ကြည့်ပါ။"
        except (ValueError, httpx.HTTPError, KeyError) as exc:
            _ = exc
            return "တောင်းဆိုမှုကို မဆောင်ရွက်နိုင်သေးပါ။ Product ID၊ ဖုန်းနံပါတ်နှင့် stock ကို ပြန်စစ်ပြီး ထပ်ကြိုးစားပါ။"
