# MY CASE v1 — Telegram T6 Durable Central Cart

## Objective

T6 establishes one durable, canonical, Customer-owned cart shared by the Telegram Bot, Telegram Mini App, and future authenticated Website consumers. The Central FastAPI backend and PostgreSQL database remain the business authority.

## Current architecture

```text
Telegram Bot ─────┐
Telegram Mini App ─┼──> Central CartService/API ───> Central Database
Website ──────────┘
```

The existing `Cart` and `CartItem` models are reused. No `telegram_carts`, `telegram_cart_items`, `mini_app_carts`, or `website_carts` tables were created.

## Ownership and integrity

A cart is owned by the canonical `Customer`. The reusable `CartService` receives the server-derived Customer ID and never accepts a client-supplied Customer ID as authorization. The existing unique Customer constraint enforces one active cart per Customer, and the existing `(cart_id, product_id)` uniqueness constraint prevents duplicate product rows.

Cart operations validate active product existence and quantities from 1 through 999. Prices, line totals, item counts, and display data are calculated server-side. Client-provided price, subtotal, stock, product name, SKU, and Customer ID are not trusted.

Cart item reads and mutations use the existing foreign keys, row locks, and constraints. PostgreSQL concurrency testing remains environment-limited and is not claimed as passed.

## Central API

The new reusable customer-authenticated API is versioned through the existing application prefix:

- `GET /api/v1/carts/current`
- `POST /api/v1/carts/current/items`
- `PATCH /api/v1/carts/current/items/{item_id}`
- `DELETE /api/v1/carts/current/items/{item_id}`
- `DELETE /api/v1/carts/current/items`

Ownership derives from the authenticated User’s canonical `customer_id`. Users without a provisioned Customer receive a safe conflict response. Existing Telegram `/telegram/cart` compatibility routes remain available and now delegate read/set/remove operations to the same reusable CartService.

## Bot and Mini App

The Bot continues using verified Telegram identity headers and the existing Telegram compatibility routes, which share the central CartService and durable database. Its process-local map is retained only as an anonymous/unlinked fallback and is not authoritative after a verified Customer cart is available.

The Mini App loads the server cart for a linked Telegram identity and keeps browser localStorage only as an anonymous/temporary fallback. An authenticated server cart cannot be silently overwritten by localStorage. Changes made through the Bot and Mini App therefore converge on the same central cart after identity linking.

The Website’s existing anonymous/local behavior is preserved. No new Website authentication or cart handoff assumptions were invented.

## Checkout boundary

The existing Central checkout path remains authoritative. It locks the customer cart and items, re-reads current product and inventory state through the existing order service, creates the Central Order, decrements inventory through the existing authority, and clears cart items only after successful order creation. Existing checkout idempotency behavior is preserved. Payment is not part of T6.

## Tests and verification

T6-focused tests cover cart model constraints, reusable service operation surface, customer-scoped route shape, and server-side quantity/product validation. The full executable Python suite passed with 27 tests, including Bot and existing Telegram regression tests. MyPy, scoped Ruff, Python compilation, and `git diff --check` passed.

PostgreSQL integration/concurrency tests and Playwright remain `NOT RUN — ENVIRONMENT LIMITATION`. The final Mini App package gate is also `NOT RUN — ENVIRONMENT LIMITATION` because the migrated pnpm workspace requests a destructive dependency reinstall; that reinstall was declined.

## Deferred T7+

T7 and later phases remain deferred. Customer order history, payments, delivery, loyalty, promotions, returns/refunds, production deployment, and unrelated R5 work were not started.
