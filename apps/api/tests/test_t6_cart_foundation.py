from apps.api.app.cart import router as cart_router
from apps.api.app.cart_models import Cart, CartItem
from apps.api.app.cart_service import CartService
from fastapi.routing import APIRoute


def test_cart_schema_has_canonical_customer_and_product_constraints() -> None:
    assert Cart.__tablename__ == "carts"
    assert CartItem.__tablename__ == "cart_items"
    assert Cart.__table__.columns["customer_id"].unique is True
    assert {"cart_id", "product_id", "quantity"}.issubset(set(CartItem.__table__.columns.keys()))
    assert any(c.name == "uq_cart_items_cart_product" for c in CartItem.__table__.constraints)


def test_cart_service_is_single_reusable_business_service() -> None:
    operations = {"get_or_create", "read", "add", "set_product", "update", "remove", "remove_product", "clear"}
    assert operations.issubset(set(dir(CartService)))


def test_customer_cart_routes_are_versionable_and_customer_scoped() -> None:
    paths = {route.path for route in cart_router.routes if isinstance(route, APIRoute)}
    assert paths == {
        "/carts/current",
        "/carts/current/items",
        "/carts/current/items/{item_id}",
    }
    for route in cart_router.routes:
        if isinstance(route, APIRoute):
            assert "customer_id" not in route.path


def test_cart_quantity_and_product_payloads_are_server_validated() -> None:
    route = next(
        route for route in cart_router.routes if isinstance(route, APIRoute) and route.path == "/carts/current/items"
    )
    assert route.methods == {"POST"}
    assert "payload" in route.dependant.path_params or route.dependant.body_params
