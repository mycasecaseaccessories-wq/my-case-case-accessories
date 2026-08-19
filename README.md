# My Case v1

My Case is a modular-monolith commerce platform with one Central Backend, one Central PostgreSQL source of truth, and four clients: Customer Website, Admin, POS, and Telegram.

## B00 status

B00 — Engineering Foundation is authorized and limited to framework scaffolding, local development configuration, quality tooling, API foundation, and application shells. **Business modules are not implemented.**

Not implemented in B00: products, variants, device compatibility, inventory, reservations, customers, carts, checkout, orders, payments, payment evidence, pre-orders, delivery, POS sales/shifts, returns, loyalty, promotions, Telegram commerce, reports, and business notifications.

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

Alembic is initialized under `apps/api/alembic`. B00 intentionally creates **no Phase 1.2 business tables and no speculative tables**. Business schema implementation belongs to the later approved database milestone.

## Environment safety

Development, test, staging, and production use separate configuration and data. Never commit `.env` files or real secrets. Development and test data must be synthetic; production customer data must not be casually copied into development.
