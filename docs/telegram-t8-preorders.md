# MY CASE v1 — Telegram T8 Pre-Order Workflow

## Scope

T8 adds a minimal pre-order specialization for Telegram Bot and Mini App on top of the existing Central Order architecture. A pre-order is not an independent sales truth.

```text
Canonical Customer → Order → OrderItem → PreOrder
```

The `Order` and `OrderItem` records remain authoritative for customer, product, quantity, price, and total. `PreOrder` stores only specialization state, the linked order/item references, customer ownership, deposit state, and retry metadata.

## Eligibility and transaction

Products have a minimal `pre_order_eligible` flag exposed through catalog read/write schemas. T8 validates active product, eligibility, positive quantity, and the authenticated canonical Customer. Pre-order creation creates the Central Order, its OrderItem price snapshot, and the linked PreOrder in one transaction. Normal inventory is not decremented for pre-orders; reservation/fulfillment policy is outside T8.

## API

Customer routes:

- `POST /api/v1/pre-orders`
- `GET /api/v1/pre-orders`
- `GET /api/v1/pre-orders/{pre_order_id}`

Telegram route:

- `POST /api/v1/telegram/pre-orders`

Admin routes:

- `GET /api/v1/pre-orders/admin/list`
- `PATCH /api/v1/pre-orders/{pre_order_id}`

Customer and Telegram ownership is derived server-side. The client cannot select a customer. Admin operations use the existing admin authorization dependency.

## Status and deposit boundary

Pre-order status and `deposit_state` are separate fields. The initial status is `requested` and the initial deposit state is `not_required`. No rule equates deposit approval with pre-order confirmation. Admin status/deposit updates are explicit and policy-configurable. No payment gateway, provider SDK, automated payment verification, receipt storage, or payment-success simulation was added.

## Bot and Mini App

The Bot supports `/preorder <product_id> [quantity]`, checks server-provided eligibility, and creates the Central-linked pre-order with an idempotency key. The Mini App displays a Pre-order action only for eligible products, requires verified linked Telegram identity, sends the request to the Central API, and shows loading/success/error feedback. Existing catalog/cart/order behavior is preserved.

## Migration

Forward migration `0009_preorders.py` adds the product eligibility field and `pre_orders` table with foreign keys to `orders`, `order_items`, and `customers`, plus unique order-item and retry-key constraints. Existing migrations `0001–0008` were not rewritten or deleted.

## Admin, POS, Website

Admin has only the minimal view/update operations required by T8. POS pre-order redesign was not started. Website pre-order UI was not added because a compatible authenticated workflow is not available; no second authentication system was invented. Existing POS and Website behavior remains unchanged.

## Verification and limitations

The executable Python suite passed with 34 tests. MyPy, scoped Ruff, Python compile, and diff hygiene passed. PostgreSQL integration/concurrency, Playwright, and final package-level frontend verification remain environment-limited where dependencies are unavailable. These are reported as `NOT RUN — ENVIRONMENT LIMITATION`.

## Deferred T9+

Payment gateway/evidence implementation, delivery, fulfillment, loyalty, promotions, returns/refunds, live production deployment, inventory reservation, and T9+ work remain deferred.
