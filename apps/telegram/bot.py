from dataclasses import dataclass, field
from uuid import UUID, uuid4

import httpx

from .commerce import CommerceApiClient, format_product_detail, format_product_menu


@dataclass
class CartLine:
    product_id: UUID
    quantity: int = 1


@dataclass
class TelegramCommerceBot:
    api: CommerceApiClient
    mini_app_url: str | None = None
    carts: dict[int, dict[UUID, CartLine]] = field(default_factory=dict)

    def start_markup(self) -> dict[str, object] | None:
        if not self.mini_app_url:
            return None
        return {
            "inline_keyboard": [
                [{"text": "Open My Case Store", "web_app": {"url": self.mini_app_url}}]
            ]
        }

    def _cart(self, chat_id: int) -> dict[UUID, CartLine]:
        return self.carts.setdefault(chat_id, {})

    async def handle_text(self, chat_id: int, text: str) -> str:
        try:
            command, _, argument = text.strip().partition(" ")
            command = command.casefold()
            if command in {"/start", "/help"}:
                return (
                    "My Case သို့ ကြိုဆိုပါတယ်။\n"
                    "/categories - Category စာရင်း\n"
                    "/products - Product စာရင်း\n"
                    "/search <စကားလုံး> - ရှာရန်\n"
                    "/product <id> - အသေးစိတ်\n"
                    "/add <id> [အရေအတွက်] - Cart ထဲထည့်ရန်\n"
                    "/set <id> <အရေအတွက်> - Cart quantity ပြောင်းရန်\n"
                    "/remove <id> - Cart မှ ဖယ်ရန်\n"
                    "/cart - Cart ကြည့်ရန်\n"
                    "/checkout <အမည်> | <ဖုန်း> - Order တင်ရန်\n"
                    "/orders - မိမိ order များ\n"
                    "/order <order-id> - Order အသေးစိတ်\n"
                    "/status <order-id> - Order status"
                )
            if command == "/categories":
                categories = await self.api.list_categories()
                return (
                    "\n".join(
                        f"{index}. {item['name']}"
                        for index, item in enumerate(categories, 1)
                    )
                    or "Category မရှိသေးပါ။"
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
                central_add = getattr(self.api, "add_cart_item", None)
                if callable(central_add):
                    try:
                        await central_add(chat_id, product_id, quantity)
                        return "Cart ထဲသို့ ထည့်ပြီးပါပြီ။ /cart ဖြင့် စစ်ဆေးနိုင်ပါတယ်။"
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code != 409:
                            raise
                self._cart(chat_id)[product_id] = CartLine(product_id, quantity)
                return "Cart ထဲသို့ ထည့်ပြီးပါပြီ။ /checkout ပြုလုပ်ပါက Central cart သို့ သိမ်းပါမည်။"
            if command == "/set":
                parts = argument.split()
                if len(parts) != 2:
                    return "Format: /set <product-id> <အရေအတွက်>"
                product_id = UUID(parts[0])
                quantity = int(parts[1])
                if quantity < 1 or quantity > 999:
                    return "အရေအတွက်သည် 1 မှ 999 အတွင်း ဖြစ်ရပါမည်။"
                central_set = getattr(self.api, "set_cart_item", None)
                if callable(central_set):
                    try:
                        await central_set(chat_id, product_id, quantity)
                        return "Cart အရေအတွက်ကို ပြောင်းပြီးပါပြီ။"
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code != 409:
                            raise
                self._cart(chat_id)[product_id] = CartLine(product_id, quantity)
                return "Cart အရေအတွက်ကို ပြောင်းပြီးပါပြီ။"
            if command == "/remove":
                product_id = UUID(argument.strip())
                central_remove = getattr(self.api, "remove_cart_item", None)
                if callable(central_remove):
                    try:
                        await central_remove(chat_id, product_id)
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code != 409:
                            raise
                self._cart(chat_id).pop(product_id, None)
                return "Cart မှ ဖယ်ရှားပြီးပါပြီ။"
            if command == "/cart":
                central_get = getattr(self.api, "get_cart", None)
                if callable(central_get):
                    try:
                        central = await central_get(chat_id)
                        if not central.get("items"):
                            return "Cart လွတ်နေပါတယ်။ /products ဖြင့် စတင်ရွေးချယ်ပါ။"
                        lines = [
                            f"{index}. {item['product_name']} × {item['quantity']} = {item['line_total']} MMK"
                            for index, item in enumerate(central["items"], 1)
                        ]
                        return "\n".join(lines) + f"\n\nစုစုပေါင်း: {central['total']} MMK"
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code != 409:
                            raise
                cart = self._cart(chat_id)
                if not cart:
                    return "Cart လွတ်နေပါတယ်။ /products ဖြင့် စတင်ရွေးချယ်ပါ။"
                lines = []
                for index, line in enumerate(cart.values(), 1):
                    product = await self.api.get_product(line.product_id)
                    lines.append(
                        f"{index}. {product.name} × {line.quantity} = {product.price * line.quantity:.2f} MMK"
                    )
                return "\n".join(lines) + "\n\nOrder တင်ရန် /checkout အမည် | ဖုန်း"
            if command == "/checkout":
                parts = [part.strip() for part in argument.split("|")]
                if len(parts) != 2 or not all(parts):
                    return "Format: /checkout အမည် | ဖုန်း"
                cart = self._cart(chat_id)
                link = getattr(self.api, "link_telegram_customer", None)
                checkout = getattr(self.api, "checkout_cart", None)
                if not cart and not (callable(link) and callable(checkout)):
                    return "Cart လွတ်နေပါတယ်။"
                if callable(link) and callable(checkout):
                    try:
                        await link(chat_id, parts[0], parts[1])
                        for line in cart.values():
                            await self.api.set_cart_item(
                                chat_id, line.product_id, line.quantity
                            )  # type: ignore[attr-defined]
                        order = await checkout(chat_id, f"telegram:{chat_id}:{uuid4()}")
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code == 409:
                            return "Telegram account ကို authenticated Customer account နဲ့ link ပြီးမှ checkout လုပ်နိုင်ပါမယ်။"
                        raise
                else:
                    customer = await self.api.find_or_create_customer(
                        parts[0], parts[1]
                    )
                    customer_id = UUID(str(customer["id"]))
                    order = await self.api.create_order(
                        customer_id,
                        parts[0],
                        parts[1],
                        [
                            {
                                "product_id": str(line.product_id),
                                "quantity": line.quantity,
                            }
                            for line in cart.values()
                        ],
                    )
                cart.clear()
                return f"Order တင်ပြီးပါပြီ။ Order ID: {order['id']}\nStatus: {order['status']}\nစုစုပေါင်း: {order['total']} MMK"
            if command in {"/orders", "/history"}:
                list_orders = getattr(self.api, "list_customer_orders", None)
                if not callable(list_orders):
                    return "Order history API မရသေးပါ။"
                orders = await list_orders(chat_id)
                if not orders:
                    return "မိမိ၏ order history မရှိသေးပါ။"
                return "\n".join(
                    f"{order['id']} · {order['status']} · {order['total']} MMK · {order.get('created_at', '')}"
                    for order in orders
                )
            if command in {"/order", "/status"}:
                if not argument.strip():
                    return "Order ID ထည့်ပေးပါ။"
                get_customer_order = getattr(self.api, "get_customer_order", None)
                if not callable(get_customer_order):
                    return "Customer-owned order API မရသေးပါ။"
                order = await get_customer_order(chat_id, UUID(argument.strip()))
                item_lines = "\n".join(
                    f"- {item['product_name']} × {item['quantity']}"
                    for item in order.get("items", [])
                )
                return (
                    f"Order ID: {order['id']}\nDate: {order.get('created_at', '')}\n"
                    f"Status: {order['status']}\nစုစုပေါင်း: {order['total']} MMK\n{item_lines}"
                )
            return "မသိသော command ဖြစ်ပါတယ်။ /help ဖြင့် အသုံးပြုနိုင်သော command များကို ကြည့်ပါ။"
        except (ValueError, httpx.HTTPError, KeyError) as exc:
            _ = exc
            return "တောင်းဆိုမှုကို မဆောင်ရွက်နိုင်သေးပါ။ Product ID၊ ဖုန်းနံပါတ်နှင့် stock ကို ပြန်စစ်ပြီး ထပ်ကြိုးစားပါ။"
