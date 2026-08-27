# B00 Engineering Foundation

B00 establishes the repository, application shells, API foundation, local PostgreSQL orchestration, shared boundaries, quality checks, and CI checks. It deliberately does not implement any Phase 1.2 business tables, business APIs, customer flows, inventory, payments, orders, POS workflows, or Telegram commerce.

## Deferred decisions

Payment and delivery providers, object storage, POS scanner/printer integrations, Telegram library and secure handoff, promotion stacking, mixed-cart fulfillment, pre-order confirmation policy, worker/queue provider, and production hosting remain deferred until their approved milestones.

## Developer commands

The root README is the source for local setup and checks. Backend commands run from `apps/api`; frontend commands run from each shell directory. The local PostgreSQL service is defined in `infrastructure/docker-compose.yml` and uses development-only credentials.
