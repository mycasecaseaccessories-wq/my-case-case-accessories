# My Case Telegram-first commerce channel

This package is a channel adapter over the existing Central API. It does not own business data, customers, inventory, carts, or orders. Product, stock, customer, cart, and order truth remains in the Central Backend and Central Database.

## Configuration

Set `TELEGRAM_BOT_TOKEN` and `CENTRAL_API_BASE_URL` in the environment. The default transport is long polling (`TELEGRAM_MODE=polling`). Webhook mode requires `TELEGRAM_MODE=webhook`, `TELEGRAM_WEBHOOK_URL`, and `TELEGRAM_WEBHOOK_SECRET_TOKEN`.

The token is never hard-coded. Startup fails when the token is absent. Webhook mode fails closed when its URL or secret token is absent, registers the secret with Telegram, and verifies the `X-Telegram-Bot-Api-Secret-Token` header on every update.

## Customer identity and durable commerce flow

The Mini App sends Telegram WebApp `initData` to the Central Backend for cryptographic verification. The Bot uses the server-side bot token boundary. A verified Telegram identity is linked explicitly to the canonical Central Customer using the customer’s exact phone number; display names, usernames, arbitrary customer IDs, and request-body Telegram IDs are not identity authority. Conflicting links return a safe conflict response and are never silently merged.

After linking, `/add`, `/cart`, `/set`, and `/remove` operate on the customer-owned Central cart. The cart survives Bot process restarts and is shared with the Mini App. Anonymous pre-link Bot state is only a temporary fallback and is not authoritative. `/checkout Name | Phone` links the customer when needed, transfers temporary lines to the Central cart, and checks out through the Central order transaction. Checkout accepts an idempotency key so a retry cannot create a duplicate order.

## Supported customer order flow

`/orders` and `/history` list only orders owned by the verified canonical Customer. `/order <uuid>` and `/status <uuid>` return only customer-safe date, status, total, and item information. A non-owned order is returned as not found without disclosing ownership. The Mini App provides the equivalent My Orders, order detail, and status views.

The customer-facing routes are separate from admin order routes. Admin catalog, inventory, and order authorization remain unchanged. Payment, delivery, promotion, fulfillment, and the secure Website session handoff remain outside this milestone until their approved contracts and production infrastructure exist.

## Run

From the repository root:

```bash
python -m apps.telegram.main
```

The implementation can also be embedded by constructing `TelegramCommerceBot`, `CommerceApiClient`, and `TelegramApi` from an application runner.
