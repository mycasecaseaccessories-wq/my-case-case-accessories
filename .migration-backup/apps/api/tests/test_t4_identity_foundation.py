from apps.api.app.auth import User
from apps.api.app.auth import router as auth_router
from apps.api.app.telegram_models import ExternalIdentity
from fastapi.routing import APIRoute


def test_t4_external_identity_is_provider_neutral() -> None:
    assert ExternalIdentity.__tablename__ == "external_identities"
    columns = ExternalIdentity.__table__.columns
    column_names = set(columns.keys())
    assert {"provider", "provider_subject", "customer_id", "last_verified_at"}.issubset(column_names)
    assert "telegram_user_id" not in column_names


def test_authenticated_user_can_reference_canonical_customer() -> None:
    assert User.__table__.columns["customer_id"].nullable is True
    assert User.__table__.columns["customer_id"].foreign_keys


def test_t4_auth_routes_exist() -> None:
    routes = {route.path for route in auth_router.routes if isinstance(route, APIRoute)}
    assert "/auth/telegram/verify" in routes
    assert "/auth/telegram/link" in routes
    assert "/auth/telegram/me" in routes


def test_t4_migration_is_forward_from_current_head() -> None:
    migration = __import__(
        "apps.api.alembic.versions.0008_t4_external_identity_account", fromlist=["revision"]
    )
    assert migration.down_revision == "0007_external_identity_checkout_idempotency"
