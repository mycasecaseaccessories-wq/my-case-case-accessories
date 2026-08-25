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

The final system must provide one canonical customer identity shared across Website, POS, Admin, and Telegram where applicable. At the time of the original decision record, the implementation did not satisfy this requirement. The subsequent R1–R3 reconciliation introduced a canonical customer foundation, exact email/phone duplicate prevention, `orders.customer_id`, website association, and POS association. Addresses and authenticated customer ownership remain future work because the detailed locked baseline artifacts are not available in the repository.

This remains a **REQUIRED FUTURE CORRECTION** for address/ownership completion; the R1–R3 customer foundation is now implemented in commit `24df9ba`.

## 6. Security status

The current implementation remains **NOT PRODUCTION READY**. R1–R3 added admin-role protection to catalog writes, inventory access/adjustment, and order list/detail routes, and removed the production default-secret fallback by requiring configured `JWT_SECRET` in production/staging. Remaining gaps include full POS authorization, order ownership, complete frontend route protection, token lifecycle hardening, and broader security policy decisions.

The R2 changes are recorded as implemented in commit `24df9ba`; the remaining gaps require a future authorized hardening milestone.

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

No endpoint was changed in the original documentation-only decision task. R1–R3 subsequently added customer endpoints and authorization changes under the separate implementation authorization.

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

Further implementation may proceed only when the corresponding milestone is explicitly authorized. R4 Catalog Normalization is now separately authorized by `Pasted_content_16.txt`; R5 must not start until R4 is completed and verified.

## 10. Verification and change boundary

The original task was documentation/governance only and was committed as `78307a0`. The subsequent R1–R3 implementation authorization produced commit `24df9ba`. This document is now updated to record the actual R4 authorization and current reconciliation status; no R4 schema migration, variant, device-compatibility, media, or availability-policy decision is claimed without the locked baseline artifacts.

**Explicit R4 boundary:** R4 may modify catalog implementation only. It must not start R5 inventory/reservations, payments, delivery, loyalty, promotions, returns/refunds, or live Telegram integration.


## 11. R4 Catalog Normalization status

R4 was authorized by `Pasted_content_16.txt` and has been implemented as a partial, data-safe catalog normalization milestone. Existing `categories` and `products` tables, SKU uniqueness, stable UUID identifiers, slug validation, active-status filtering, customer search/filter behavior, and POS product lookup were retained. Admin now has protected category/product write behavior and product active/inactive status updates through `PATCH /api/v1/catalog/categories/{category_id}` and `PATCH /api/v1/catalog/products/{product_id}`.

No R4 schema migration was required because the accessible baselines did not define a canonical variant, device-compatibility, media, or availability schema. The missing detailed Phase 1.2/1.3/1.4 artifacts are recorded as **BASELINE ARTIFACT NOT PRESENT IN REPOSITORY**. Accordingly, the following remain explicitly unresolved rather than invented: Product vs Product Variant separation; device compatibility; product media/storage; separate stock, commercial, and fulfillment availability policy; pagination/search API contract; and product detail/availability behavior beyond the existing active-status model.

R4 verification added catalog validation tests for safe slugs, SKU presence, non-negative prices, and status updates. The final R4 verdict is **B. R4 PARTIAL — CONTINUE R4**, because the safe normalization and admin status behavior are implemented, while baseline-dependent catalog concepts cannot be completed without the locked design artifacts. R5 Inventory/Reservation work has not been started.
