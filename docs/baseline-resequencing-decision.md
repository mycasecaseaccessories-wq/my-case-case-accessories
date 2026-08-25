# MY CASE v1 — Baseline Resequencing & Retention Decision

**Decision status:** Approved by user for retention and resequencing  
**Repository:** `mycasecaseaccessories-wq/my-case-case-accessories`  
**Decision baseline commit:** `c669d4b`  
**Decision record date:** 2026-08-24

## 1. Decision

The previously identified baseline conflict is resolved by an explicit user decision:

> **BASELINE RESEQUENCED — IMPLEMENTATION RETAINED**

The existing Catalog, Inventory, Storefront, Cart/Checkout, Orders, Admin, POS, Authentication, and Telegram adapter work is retained as an **early commerce MVP/prototype implementation**. It is not automatically approved as the final canonical My Case schema or API.

No source code, database schema, API contract, migration history, or existing commit was deleted, reset, reverted, rewritten, or changed for this decision record.

## 2. Governance context

The repository’s B00 document states that business tables, business APIs, customer flows, inventory, orders, POS workflows, and Telegram commerce were deferred. The implementation audit found that later commits introduced those areas. The user has decided to retain that work because substantial implementation exists, Git history is clean, the foundation remains usable, and deletion or rollback would create unnecessary rework.

This record changes the **roadmap classification**, not the technical approval status. The implementation remains prototype/MVP work until it is reconciled against the locked project baselines.

## 3. Locked design baselines

The authoritative baselines remain:

| Baseline | Status in this repository |
|---|---|
| Phase 1.1 — Requirements | Baseline artifact not present in repository; use the externally approved governance version. |
| Phase 1.2 — Database Schema & ERD v1.1 | Baseline artifact not present in repository; do not invent a replacement. |
| Phase 1.3 — UI/UX Specification v1.1 | Baseline artifact not present in repository; use the externally approved governance version. |
| Phase 1.4 — API Specification v1.1 | Baseline artifact not present in repository; do not infer approval from current routes. |
| Phase 1.5 — Development Milestones & Implementation Plan v1.0 | Baseline artifact not present in repository; the sequence below is proposed only. |

The absence of these artifacts is recorded as **BASELINE ARTIFACT NOT PRESENT IN REPOSITORY**. No missing specification has been recreated or assumed.

## 4. Existing implementation classification

The following is retained as prototype/MVP work and is not production-ready: catalog management; inventory and stock adjustment; storefront product listing and search; browser-local cart; basic checkout and order creation; admin dashboard; basic POS; Telegram commerce API adapter; and basic authentication with a custom signed bearer token.

The existing MVP data model consists of `categories`, `products`, `inventory_items`, `stock_movements`, `orders`, `order_items`, and `users`. These tables are **not automatically canonical**. They must be reconciled with the approved Phase 1.2 model before production schema approval.

## 5. Customer identity requirement

The final system must provide one canonical customer identity shared across Website, POS, Admin, and Telegram where applicable. The current implementation does not satisfy this requirement. It has no canonical customer table, sends website name/phone directly to an order, uses the literal `Walk-in customer`/`POS` identity for POS sales, and has no phone matching, email matching, duplicate detection, or safe merge.

This is recorded as a **REQUIRED FUTURE CORRECTION**. No matching or merging logic is implemented in this decision-record task.

## 6. Security status

The current implementation is **NOT PRODUCTION READY**. The known gaps are business endpoints that are not consistently protected, no enforced admin role on sensitive APIs, no POS authorization, no order ownership checks, incomplete frontend route protection, production risks in the custom bearer token, and a default secret fallback when `JWT_SECRET` is absent.

These gaps are recorded for future hardening. They were not fixed in this documentation/governance task.

## 7. Schema reconciliation requirement

Before approving a production schema, the retained MVP model must be reconciled against the approved Phase 1.2 model. The reconciliation must explicitly evaluate categories; products; variants/SKU; devices and device compatibility; product media; inventory; warehouses; reservations; customers; addresses; orders; order items; payments; payment allocations; payment evidence; pre-orders; delivery; returns/refunds; loyalty; promotions; notifications; and audit logs.

Existing migrations `0001_catalog`, `0002_inventory`, `0003_orders`, and `0004_users` must not be deleted or rewritten. Any future restructuring must use forward migrations, preserve existing data, document field/table mappings, and avoid destructive changes unless separately approved.

## 8. API reconciliation requirement

Current routes are prototype routes. Before production use, each route must be compared with Phase 1.4 API Specification v1.1 using the following decision fields:

| Existing endpoint group | Intended canonical endpoint | Decision | Reason |
|---|---|---|---|
| Catalog routes | To be determined from Phase 1.4 | Keep/Modify/Replace/Deprecate pending reconciliation | Current contract is prototype-only. |
| Inventory routes | To be determined from Phase 1.4 | Keep/Modify/Replace/Deprecate pending reconciliation | Authorization and canonical stock model are unresolved. |
| Order/checkout routes | To be determined from Phase 1.4 | Keep/Modify/Replace/Deprecate pending reconciliation | Customer identity, payment, and status model are incomplete. |
| Auth routes | To be determined from Phase 1.4 and B02 decision | Keep/Modify/Replace/Deprecate pending reconciliation | Custom token and role enforcement require approval. |
| POS integration | To be determined from Phase 1.4 | Keep/Modify/Replace/Deprecate pending reconciliation | POS currently reuses generic order creation. |
| Telegram adapter | To be determined from Phase 1.4 | Keep/Modify/Replace/Deprecate pending reconciliation | Adapter exists without live webhook/polling. |

No endpoint was changed in this task.

## 9. Proposed milestone resequencing

The following sequence is a proposal only. It is **not approved** until reconciled with Phase 1.5:

| Proposed milestone | Scope |
|---|---|
| R0 | Baseline reconciliation |
| R1 | Canonical database alignment |
| R2 | Authentication/RBAC hardening |
| R3 | Customer identity and addresses |
| R4 | Catalog normalization |
| R5 | Inventory and reservation foundation |
| R6 | Cart and checkout |
| R7 | Orders |
| R8 | Pre-orders and deposits |
| R9 | Payments |
| R10 | Delivery and fulfillment |
| R11 | POS |
| R12 | Telegram live integration |
| R13 | Loyalty and membership |
| R14 | Promotions |
| R15 | Returns and refunds |
| R16 | Notifications |
| R17 | Reporting and admin hardening |
| R18 | Full integration and UAT |

Further implementation must stop after this decision record until the next milestone is explicitly authorized.

## 10. Verification and change boundary

This task is documentation/governance only. The required verification is that only this decision record is added, source code is unchanged, migrations are unchanged, and existing Git history is unchanged. The commit for this record must be:

```text
docs: approve MVP retention and baseline resequencing
```

**Explicit statement:** No Python, TypeScript, SQLAlchemy model, Alembic migration, endpoint, authentication behavior, POS behavior, inventory behavior, order behavior, or Telegram behavior was changed in this task.
