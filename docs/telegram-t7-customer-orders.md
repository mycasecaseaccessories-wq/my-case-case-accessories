# MY CASE v1 — Telegram T7 Customer-Owned Orders

## Objective

T7 exposes secure customer-owned order history, order detail, and current customer-visible status through the Central API. The Central Order and OrderItem models remain the source of truth.

## API

The new authenticated customer routes use the existing API version prefix:

- `GET /api/v1/customer/orders`
- `GET /api/v1/customer/orders/{order_id}`

The list route uses bounded `offset`/`limit` pagination, newest-first ordering with a stable ID tie-breaker, and database-side `Order.customer_id` filtering. The detail route combines the order ID and authenticated Customer ID in the database query and returns a non-leaking `404` when the order is absent or belongs to another customer.

Existing admin `GET /orders` and `GET /orders/{order_id}` routes remain separately authorized and were not weakened or exposed to customers.

## Ownership and security

Customer ownership is derived from the authenticated User’s server-side canonical `customer_id`. No customer ID, Telegram ID, phone, email, or order owner is accepted from the client as authorization. Telegram compatibility routes continue resolving the canonical Customer from the verified external identity. Customer responses do not expose admin-only metadata, secrets, raw authentication payloads, or payment/delivery-provider data.

## Order data and money

The response uses the authoritative Order total, status, created timestamp, and OrderItem `unit_price` snapshot. Historical totals are not recalculated from current product prices. Product name and SKU are included from the existing product relation because the current order model does not maintain name/SKU snapshots; no order-accounting redesign was introduced. Money remains MMK-only.

## Bot and Mini App

The existing Bot `/orders`, `/history`, `/order`, and `/status` flows use customer-owned Central order operations and do not fetch all orders for presentation filtering. The Mini App loads the customer-owned order list and fetches selected detail through the authenticated Telegram context. Loading, empty, error, retry, and session/unlinked states remain customer-safe. Order history is not stored in localStorage.

## Website compatibility

The Website’s existing authenticated customer order integration was not replaced or given a second authentication system. The generic `/customer/orders` route is available for an existing authenticated User/Customer context. Website-specific UI integration remains deferred where the current Website architecture does not expose a compatible customer session.

## Tests and verification

T7-focused tests cover route separation from admin routes, no client customer-ID route authority, bounded pagination, historical `OrderItem.unit_price`, and existing Bot/Telegram regression behavior. The final executable Python suite passed with 31 tests; MyPy, scoped Ruff, Python compile, and `git diff --check` passed.

PostgreSQL integration/concurrency and Playwright/browser checks remain `NOT RUN — ENVIRONMENT LIMITATION` where unavailable. The Mini App package gate must be reported separately if pnpm requires a destructive dependency reinstall.

## Deferred T8+

T8 and later phases remain deferred. Payment, delivery, fulfillment, loyalty, promotions, returns/refunds, production deployment, and unrelated R5 work were not started.
