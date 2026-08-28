from apps.api.app.customer_orders import router
from apps.api.app.orders import OrderItem
from fastapi.routing import APIRoute


def test_customer_order_routes_are_separate_from_admin_routes() -> None:
    routes = {
        (route.path, tuple(sorted(route.methods or set()))) for route in router.routes if isinstance(route, APIRoute)
    }
    assert ("/customer/orders", ("GET",)) in routes
    assert ("/customer/orders/{order_id}", ("GET",)) in routes


def test_customer_order_routes_do_not_accept_customer_id() -> None:
    for route in router.routes:
        if isinstance(route, APIRoute):
            assert "customer_id" not in route.path
            assert "user" in route.dependant.dependencies[0].name or route.dependant.dependencies


def test_order_item_keeps_historical_unit_price_snapshot() -> None:
    assert "unit_price" in OrderItem.__table__.columns


def test_customer_order_list_has_bounded_pagination() -> None:
    route = next(route for route in router.routes if isinstance(route, APIRoute) and route.path == "/customer/orders")
    query_names = {param.name for param in route.dependant.query_params}
    assert {"offset", "limit"}.issubset(query_names)
