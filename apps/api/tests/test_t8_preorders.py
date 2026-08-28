from apps.api.app.catalog_models import Product
from apps.api.app.preorder_models import PreOrder
from apps.api.app.preorders import router, telegram_router
from fastapi.routing import APIRoute


def test_preorder_is_linked_to_central_order_and_item() -> None:
    assert PreOrder.__tablename__ == "pre_orders"
    assert {"order_id", "order_item_id", "customer_id", "status", "deposit_state"}.issubset(
        set(PreOrder.__table__.columns.keys())
    )
    assert "pre_order_eligible" in Product.__table__.columns


def test_preorder_routes_are_separate_and_customer_scoped() -> None:
    paths = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/pre-orders" in paths
    assert "/pre-orders/{pre_order_id}" in paths
    assert "/pre-orders/admin/list" in paths
    assert all("customer_id" not in route.path for route in router.routes if isinstance(route, APIRoute))
    assert any(route.path == "/telegram/pre-orders" for route in telegram_router.routes)


def test_preorder_has_separate_status_and_deposit_state() -> None:
    assert PreOrder.__table__.columns["status"].type.length == 30
    assert PreOrder.__table__.columns["deposit_state"].type.length == 30
    assert PreOrder.__table__.columns["idempotency_key"].unique is True
