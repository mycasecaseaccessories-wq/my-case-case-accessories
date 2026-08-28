# MY CASE v1 — Telegram T5 Customer Identity Foundation

## Objective

T5 establishes a secure identity foundation for the Telegram Bot and Telegram Mini App. Telegram remains an external authentication provider; the Central Customer model remains the only business customer identity.

## Architecture

```text
Telegram Bot / Mini App
        ↓ verified Telegram authentication context
Central FastAPI authentication and identity service
        ↓ provider-neutral ExternalIdentity
Canonical Customer and authenticated User
        ↓
Central database
```

No Telegram-only customer, order, cart, or business database was introduced.

## Identity model

`ExternalIdentity` stores `provider`, immutable `provider_subject`, canonical `customer_id`, timestamps, and `last_verified_at`. Telegram uses `provider="telegram"`. Display name, username, query parameters, and client-supplied customer IDs are not identity authorities.

Migration `0008_t4_external_identity_account.py` is forward-only from the actual prior head `0007_external_identity_checkout_idempotency`. It renames the existing identity table to the generic `external_identities` structure, preserves existing data, adds verification metadata, and associates authenticated `User` records with canonical Customers through an optional foreign key. Migrations `0001–0007` were not rewritten.

## Verification and linking

Telegram init data is validated with the existing HMAC-SHA256 and expiry validator. The server derives the immutable Telegram subject from verified init data. `POST /auth/telegram/verify` reports safe verification state. `GET /auth/telegram/me` resolves linked or unlinked state without returning raw auth payloads or secrets.

Explicit linking is provided by `POST /auth/telegram/link`. It requires the existing authenticated User session and verified Telegram init data. The Customer is derived from the authenticated User’s existing Customer association or authenticated account email. The endpoint does not accept a client-authoritative `customer_id`, silently create a Customer from Telegram claims, merge by display name, or match by username.

Phone/SMS verification is not present in the repository. No OTP or custom token system was invented. If a future policy uses phone linking, it must add a real verified phone ownership flow before using exact normalized phone matching.

## Bot behavior

The Bot keeps its existing catalog and commerce commands. Its Central identity path no longer performs unauthenticated Customer creation before attempting Telegram identity resolution. If an identity cannot be safely linked, the Bot returns a customer-safe instruction rather than exposing an exception or creating a duplicate Customer.

## Mini App behavior

The Mini App calls the existing verification endpoint and then the safe linked-state endpoint. A verified-but-unlinked account is shown as unlinked. Telegram checkout does not invoke the legacy phone-based link route and fails closed until the Telegram identity is linked through an authenticated Customer account. Existing non-Telegram/local fallback behavior is preserved.

## API and ownership

Customer-owned operations must resolve the Customer from the verified external identity and server-side link. The client cannot override ownership through a submitted `customer_id`. Existing customer-channel ownership dependencies remain in place for later-channel routes, while T5 adds the account-context foundation needed for future customer features.

## Tests and verification

T5 tests cover provider-neutral identity fields, canonical User-to-Customer association, auth route registration, forward migration chaining, valid/invalid/expired Telegram verification regression, and existing Telegram Bot behavior. The executable backend gate passed with `23 passed` before the final T5-only safety edits; final scoped backend verification must be rerun after those edits.

PostgreSQL integration/concurrency, Playwright, and the final Mini App package gate are environment-limited in this workspace. They must be reported as `NOT RUN — ENVIRONMENT LIMITATION`, never as fabricated passes.

## Known limitations

Customer account provisioning is currently based on the existing Website/authentication foundation. There is no SMS/OTP phone verification, unlink/recovery policy, or production identity-management UI. The repository contains preserved duplicate source trees from the workspace migration, so equivalent backend changes are mirrored in both tracked trees.

## Deferred T6+

T6 and later phases remain deferred. Durable cart redesign, full order history, payments, delivery, fulfillment, loyalty, promotions, returns/refunds, production webhook infrastructure, and unrelated R5 work are not part of T5 and were not started by this milestone.
