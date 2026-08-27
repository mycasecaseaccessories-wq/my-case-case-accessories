from apps.api.app.customer_channel import router
from apps.api.app.telegram_models import ExternalIdentity
from fastapi.routing import APIRoute


def test_customer_channel_routes_are_registered() -> None:
    routes = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/telegram/link" in routes
    assert "/telegram/cart" in routes
    assert "/telegram/cart/items/{product_id}" in routes
    assert "/telegram/cart/checkout" in routes
    assert "/telegram/orders" in routes
    assert "/telegram/orders/{order_id}" in routes


def test_external_identity_uses_provider_neutral_fields() -> None:
    columns = ExternalIdentity.__table__.columns
    assert "provider" in columns
    assert "provider_subject" in columns
    assert "customer_id" in columns


def test_identity_migration_is_forward_from_0007() -> None:
    migration = __import__(
        "apps.api.alembic.versions.0008_t4_external_identity_account", fromlist=["revision"]
    )
    assert migration.down_revision == "0007_external_identity_checkout_idempotency"
