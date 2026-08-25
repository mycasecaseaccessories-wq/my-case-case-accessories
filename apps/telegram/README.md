# My Case Telegram-first commerce channel

This package is a channel adapter over the existing Central API. It does not own business data, customers, inventory, or orders. Product, stock, customer, and order truth remains in the Central Backend and Central Database.

## Configuration

Set `TELEGRAM_BOT_TOKEN` and `CENTRAL_API_BASE_URL` in the environment. The default transport is long polling (`TELEGRAM_MODE=polling`). Webhook mode requires both `TELEGRAM_MODE=webhook` and `TELEGRAM_WEBHOOK_URL`.

The token is never hard-coded. Startup fails when the token is absent, and webhook mode fails when its URL is absent.

## Supported channel flow

`/products` lists active Central API products with MMK prices. `/search <term>` performs deterministic client-side filtering of the Central product list because no separate Telegram search contract is defined. `/product <uuid>` displays central product details. `/add <uuid> [quantity]` keeps a chat-local cart. `/checkout Name | Phone` resolves or creates the canonical Central customer and creates the order through the Central Order API, so stock is checked and deducted by the Central transaction. `/cart` displays the current cart.

Order status lookup is intentionally marked TBD because the current Central order detail endpoint is admin-protected and no approved Telegram customer-ownership or handoff-token mechanism is defined. Payment, delivery, promotion, fulfillment, and handoff policies remain deferred rather than invented.

## Run

From the repository root:

```bash
python -m apps.telegram.main
```

The implementation can also be embedded by constructing `TelegramCommerceBot`, `CommerceApiClient`, and `TelegramApi` from an application runner.
