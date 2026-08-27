from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.catalog import CategoryCreate, ProductCreate, ProductUpdate


def test_category_slug_must_be_safe() -> None:
    category = CategoryCreate(name="Cases", slug="phone-cases")
    assert category.slug == "phone-cases"
    with pytest.raises(ValidationError):
        CategoryCreate(name="Cases", slug="Phone Cases")


def test_product_sku_and_price_are_validated() -> None:
    product = ProductCreate(category_id=uuid4(), name="Clear Case", slug="clear-case", sku="CASE-001", price="12.50")
    assert str(product.price) == "12.50"
    with pytest.raises(ValidationError):
        ProductCreate(category_id=uuid4(), name="Clear Case", slug="clear-case", sku="", price="12.50")
    with pytest.raises(ValidationError):
        ProductCreate(category_id=uuid4(), name="Clear Case", slug="clear-case", sku="CASE-002", price="-1")


def test_product_update_supports_status_without_removing_identity() -> None:
    update = ProductUpdate(is_active=False, sku="CASE-001")
    assert update.is_active is False
    assert update.sku == "CASE-001"
