"""Tests for the mock UCP server endpoints."""

import pytest
from fastapi.testclient import TestClient

from shopping_agent.mock_server import app, _carts, _checkout_sessions, _orders


@pytest.fixture(autouse=True)
def reset_state():
    """Reset server state before each test."""
    _carts.clear()
    _carts["default"] = []
    _checkout_sessions.clear()
    _orders.clear()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_search_products(client):
    resp = client.get("/ucp/v1/products/search", params={"q": "headphones"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["products"]) > 0
    assert any("headphones" in p["title"].lower() for p in data["products"])


def test_search_by_category(client):
    resp = client.get("/ucp/v1/products/search", params={"category": "clothing"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(p["category"] == "clothing" for p in data["products"])


def test_search_by_price_range(client):
    resp = client.get(
        "/ucp/v1/products/search",
        params={"q": "", "min_price": 100, "max_price": 200},
    )
    assert resp.status_code == 200
    for p in resp.json()["products"]:
        assert 100 <= p["price"]["amount"] <= 200


def test_get_product(client):
    resp = client.get("/ucp/v1/products/prod-001")
    assert resp.status_code == 200
    assert resp.json()["id"] == "prod-001"


def test_get_product_not_found(client):
    resp = client.get("/ucp/v1/products/nonexistent")
    assert resp.status_code == 404


def test_add_to_cart_and_view(client):
    resp = client.post(
        "/ucp/v1/cart/items",
        json={"product_id": "prod-001", "quantity": 1},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Item added to cart"

    cart = client.get("/ucp/v1/cart").json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == "prod-001"


def test_add_to_cart_increases_quantity(client):
    client.post("/ucp/v1/cart/items", json={"product_id": "prod-001", "quantity": 1})
    client.post("/ucp/v1/cart/items", json={"product_id": "prod-001", "quantity": 2})

    cart = client.get("/ucp/v1/cart").json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 3


def test_remove_from_cart(client):
    client.post("/ucp/v1/cart/items", json={"product_id": "prod-001", "quantity": 1})
    resp = client.delete("/ucp/v1/cart/items/prod-001")
    assert resp.status_code == 200

    cart = client.get("/ucp/v1/cart").json()
    assert len(cart["items"]) == 0


def test_checkout_flow(client):
    # Add item to cart
    client.post("/ucp/v1/cart/items", json={"product_id": "prod-001", "quantity": 1})

    # Create checkout session
    resp = client.post("/ucp/v1/checkout/sessions")
    assert resp.status_code == 200
    session = resp.json()
    session_id = session["session_id"]
    assert session["status"] == "created"
    assert session["total"] > 0

    # Set shipping address
    resp = client.patch(
        f"/ucp/v1/checkout/sessions/{session_id}",
        json={
            "shipping_address": {
                "name": "John Doe",
                "street": "123 Main St",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94102",
                "country": "US",
            }
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "shipping_set"

    # Complete checkout
    resp = client.post(f"/ucp/v1/checkout/sessions/{session_id}/complete")
    assert resp.status_code == 200
    order = resp.json()
    assert order["status"] == "processing"
    assert order["order_id"].startswith("ord-")
    assert order["tracking_number"].startswith("TRK")

    # Check order
    resp = client.get(f"/ucp/v1/orders/{order['order_id']}")
    assert resp.status_code == 200
    assert resp.json()["order_id"] == order["order_id"]


def test_checkout_empty_cart(client):
    resp = client.post("/ucp/v1/checkout/sessions")
    assert resp.status_code == 400


def test_checkout_without_address(client):
    client.post("/ucp/v1/cart/items", json={"product_id": "prod-001", "quantity": 1})
    session = client.post("/ucp/v1/checkout/sessions").json()
    resp = client.post(f"/ucp/v1/checkout/sessions/{session['session_id']}/complete")
    assert resp.status_code == 400
