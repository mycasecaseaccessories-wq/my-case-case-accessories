# My Case v1

My Case is a modular-monolith commerce platform with one Central Backend, one Central PostgreSQL source of truth, and four clients: Customer Website, Admin, POS, and Telegram.

## B00 status

The original B00 foundation has been extended with the first commerce milestone. Catalog, inventory, cart/checkout, orders, admin dashboard, POS, Telegram API adapter, and authentication foundations are now implemented. Payment gateway, fulfillment, returns, loyalty, and production-grade Telegram polling remain future milestones.

## Structure

```text
apps/api                 FastAPI + SQLAlchemy/Alembic foundation
apps/website             Next.js + TypeScript customer shell
apps/admin               Next.js + TypeScript admin shell
apps/pos                 Next.js + TypeScript online-first POS shell
apps/telegram            Minimal deferred Telegram boundary
packages/api-contracts   OpenAPI/contract boundary
packages/shared-types    Non-authoritative shared types
packages/test-fixtures   Synthetic test-fixture boundary
infrastructure           Docker Compose and environment notes
docs                     Engineering documentation
.github/workflows        CI foundation
```

## Prerequisites

- Python 3.11+
- Node.js 22+
- pnpm 10+
- Docker Compose (for local PostgreSQL)

## Local setup

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e './apps/api[dev]'
pnpm install
```

Start local PostgreSQL:

```bash
docker compose -f infrastructure/docker-compose.yml up -d postgres
```

Run the API:

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

Run the client shells in separate terminals:

```bash
pnpm --filter website dev
pnpm --filter admin dev
pnpm --filter pos dev
```

## Foundation endpoints

- `GET /health` proves the API process is alive.
- `GET /ready` checks PostgreSQL connectivity without exposing credentials or SQL errors.
- `GET /api/v1/foundation` confirms the versioned router foundation.

## Checks

```bash
pytest apps/api/tests
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
pnpm test:e2e
```

The B00 implementation must report any unavailable check as `NOT RUN — ENVIRONMENT LIMITATION`, not as PASS.

## Migrations

Alembic is initialized under `apps/api/alembic`. Catalog, inventory, order, and user migrations are available as revisions `0001_catalog` through `0004_users`.

## Environment safety

Development, test, staging, and production use separate configuration and data. Never commit `.env` files or real secrets. Development and test data must be synthetic; production customer data must not be casually copied into development.

## Implemented commerce features

The first commerce milestone now includes catalog, inventory, checkout, admin dashboard, POS, Telegram API adapter, and authentication foundations.

### API routes

- `GET/POST /api/v1/catalog/categories` manages active categories.
- `GET/POST /api/v1/catalog/products` lists and creates products; products require a valid category and unique SKU/slug.
- `GET /api/v1/inventory` lists stock; `POST /api/v1/inventory/{product_id}/adjust` receives or deducts stock and rejects negative inventory.
- `POST /api/v1/orders` validates stock, creates an order, and deducts inventory; `GET /api/v1/orders` lists recent orders.
- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, and `GET /api/v1/auth/me` provide the initial account and role foundation.

### Application pages

- Customer catalog and cart: `http://localhost:3000/`
- Admin catalog: `http://localhost:3001/catalog`
- Admin inventory: `http://localhost:3001/inventory`
- Admin dashboard: `http://localhost:3001/dashboard`
- Admin login: `http://localhost:3001/login`
- POS: `http://localhost:3002/`

Apply database migrations from `apps/api` with `alembic upgrade head` after PostgreSQL is running. The API also initializes metadata for convenient local development, but migrations remain the source of truth for deployed environments. Set a long random `JWT_SECRET` in `.env`; never use the example value in production. Telegram bot credentials are intentionally not committed; configure them only through deployment secrets.


## Reconciliation milestone (R1–R3)

The retained MVP now includes a forward `0005_customers` migration that adds the canonical customer foundation and a nullable `orders.customer_id` relationship without rewriting earlier migrations. The customer API provides create, exact email/phone lookup, and customer retrieval; duplicate identity candidates return `409` rather than being silently merged. Website checkout and POS sales resolve or create a canonical customer before creating an order.

Sensitive catalog writes, inventory access/adjustment, and order list/detail routes now require the existing `admin` role dependency. JWT signing uses the configured `JWT_SECRET`; production and staging configurations fail closed when it is absent, while the development fallback is explicitly development-only. Existing MVP routes remain compatible where possible, and customer name/phone order snapshots are preserved for legacy records.

The current implementation remains an MVP and is not production-ready. Customer addresses, payments, delivery, reservations, returns/refunds, and live Telegram webhook/polling remain outside this reconciliation slice because the locked detailed baseline artifacts were not available in the repository. Backend unit coverage includes password/token helper checks; typecheck, builds, Python compilation, and six API tests pass in the verification environment. Ruff still reports legacy B008/import-style findings in the existing API/migration code and requires a separate style cleanup milestone.
