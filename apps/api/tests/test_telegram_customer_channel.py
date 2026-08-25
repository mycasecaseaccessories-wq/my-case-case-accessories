from apps.api.app.customer_channel import router
from fastapi.routing import APIRoute


def test_customer_channel_routes_are_registered() -> None:
    routes = {route.path for route in router.routes if isinstance(route, APIRoute)}
    assert "/telegram/link" in routes
    assert "/telegram/cart" in routes
    assert "/telegram/cart/items/{product_id}" in routes
    assert "/telegram/cart/checkout" in routes
    assert "/telegram/orders" in routes
    assert "/telegram/orders/{order_id}" in routes
