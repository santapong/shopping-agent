"""UCP REST API client.

Wraps Google's Universal Commerce Protocol endpoints for product discovery,
cart management, checkout sessions, and order management.
"""

from __future__ import annotations

import httpx

from .models import CheckoutSession, Order, Product, Money


class UCPClient:
    """HTTP client for UCP-compliant servers."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def close(self):
        await self._client.aclose()

    # -- Product Discovery ---------------------------------------------------

    async def search_products(
        self,
        query: str = "",
        category: str = "",
        min_price: float = 0,
        max_price: float = 0,
        limit: int = 10,
    ) -> list[Product]:
        params: dict = {"q": query, "limit": limit}
        if category:
            params["category"] = category
        if min_price > 0:
            params["min_price"] = min_price
        if max_price > 0:
            params["max_price"] = max_price

        resp = await self._client.get("/ucp/v1/products/search", params=params)
        resp.raise_for_status()
        data = resp.json()
        return [_parse_product(p) for p in data.get("products", [])]

    async def get_product(self, product_id: str) -> Product:
        resp = await self._client.get(f"/ucp/v1/products/{product_id}")
        resp.raise_for_status()
        return _parse_product(resp.json())

    # -- Cart ----------------------------------------------------------------

    async def get_cart(self) -> dict:
        resp = await self._client.get("/ucp/v1/cart")
        resp.raise_for_status()
        return resp.json()

    async def add_to_cart(self, product_id: str, quantity: int = 1) -> dict:
        resp = await self._client.post(
            "/ucp/v1/cart/items",
            json={"product_id": product_id, "quantity": quantity},
        )
        resp.raise_for_status()
        return resp.json()

    async def remove_from_cart(self, product_id: str) -> dict:
        resp = await self._client.delete(f"/ucp/v1/cart/items/{product_id}")
        resp.raise_for_status()
        return resp.json()

    # -- Checkout (UCP session create / update / complete) --------------------

    async def create_checkout_session(self) -> CheckoutSession:
        resp = await self._client.post("/ucp/v1/checkout/sessions")
        resp.raise_for_status()
        return CheckoutSession(**resp.json())

    async def update_checkout_session(
        self,
        session_id: str,
        shipping_address: dict | None = None,
    ) -> CheckoutSession:
        body: dict = {}
        if shipping_address:
            body["shipping_address"] = shipping_address

        resp = await self._client.patch(
            f"/ucp/v1/checkout/sessions/{session_id}", json=body
        )
        resp.raise_for_status()
        return CheckoutSession(**resp.json())

    async def complete_checkout(self, session_id: str) -> Order:
        resp = await self._client.post(
            f"/ucp/v1/checkout/sessions/{session_id}/complete"
        )
        resp.raise_for_status()
        return Order(**resp.json())

    # -- Order Management ----------------------------------------------------

    async def get_order(self, order_id: str) -> Order:
        resp = await self._client.get(f"/ucp/v1/orders/{order_id}")
        resp.raise_for_status()
        return Order(**resp.json())

    async def list_orders(self) -> list[Order]:
        resp = await self._client.get("/ucp/v1/orders")
        resp.raise_for_status()
        data = resp.json()
        return [Order(**o) for o in data.get("orders", [])]


def _parse_product(data: dict) -> Product:
    """Parse a product dict from UCP API into a Product model."""
    price_data = data.get("price", {})
    return Product(
        id=data["id"],
        title=data["title"],
        description=data.get("description", ""),
        price=Money(
            amount=price_data.get("amount", 0),
            currency=price_data.get("currency", "USD"),
        ),
        category=data.get("category", ""),
        brand=data.get("brand", ""),
        image_url=data.get("image_url", ""),
        merchant=data.get("merchant", ""),
        in_stock=data.get("in_stock", True),
        attributes=data.get("attributes", {}),
    )
