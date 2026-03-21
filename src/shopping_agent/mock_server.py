"""Mock UCP server for local testing.

Simulates Google's Universal Commerce Protocol (UCP) endpoints with sample
product data. Run with: python -m shopping_agent.mock_server
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="Mock UCP Server", version="0.1.0")

# ---------------------------------------------------------------------------
# Sample product catalog
# ---------------------------------------------------------------------------
PRODUCTS: list[dict] = [
    {
        "id": "prod-001",
        "title": "Sony WH-1000XM5 Wireless Headphones",
        "description": "Industry-leading noise canceling with Auto NC Optimizer. Crystal clear hands-free calling. Up to 30 hours battery life.",
        "price": {"amount": 348.00, "currency": "USD"},
        "category": "electronics",
        "brand": "Sony",
        "merchant": "TechStore",
        "in_stock": True,
        "attributes": {"color": "Black", "connectivity": "Bluetooth 5.2"},
    },
    {
        "id": "prod-002",
        "title": "Apple AirPods Pro (2nd Gen)",
        "description": "Active Noise Cancellation, Adaptive Transparency, Personalized Spatial Audio with dynamic head tracking.",
        "price": {"amount": 249.00, "currency": "USD"},
        "category": "electronics",
        "brand": "Apple",
        "merchant": "TechStore",
        "in_stock": True,
        "attributes": {"color": "White", "connectivity": "Bluetooth 5.3"},
    },
    {
        "id": "prod-003",
        "title": "Samsung Galaxy S25 Ultra",
        "description": "6.9-inch Dynamic AMOLED, Snapdragon 8 Elite, 200MP camera, S Pen included, 5000mAh battery.",
        "price": {"amount": 1299.99, "currency": "USD"},
        "category": "electronics",
        "brand": "Samsung",
        "merchant": "TechStore",
        "in_stock": True,
        "attributes": {"color": "Titanium Black", "storage": "256GB"},
    },
    {
        "id": "prod-004",
        "title": "Nike Air Max 270",
        "description": "Men's running shoes with Max Air unit for comfortable cushioning. Breathable mesh upper.",
        "price": {"amount": 150.00, "currency": "USD"},
        "category": "clothing",
        "brand": "Nike",
        "merchant": "SportsFit",
        "in_stock": True,
        "attributes": {"color": "Black/White", "sizes": "7-13"},
    },
    {
        "id": "prod-005",
        "title": "Levi's 501 Original Fit Jeans",
        "description": "The original blue jean. Straight leg, button fly, sits at the waist. 100% cotton denim.",
        "price": {"amount": 69.50, "currency": "USD"},
        "category": "clothing",
        "brand": "Levi's",
        "merchant": "FashionHub",
        "in_stock": True,
        "attributes": {"color": "Medium Stonewash", "sizes": "28-42"},
    },
    {
        "id": "prod-006",
        "title": "Patagonia Better Sweater Jacket",
        "description": "Warm fleece jacket made with recycled polyester. Full-zip with stand-up collar.",
        "price": {"amount": 139.00, "currency": "USD"},
        "category": "clothing",
        "brand": "Patagonia",
        "merchant": "FashionHub",
        "in_stock": True,
        "attributes": {"color": "New Navy", "material": "Recycled Polyester"},
    },
    {
        "id": "prod-007",
        "title": "Instant Pot Duo 7-in-1 Electric Pressure Cooker",
        "description": "7 appliances in 1: pressure cooker, slow cooker, rice cooker, steamer, sauté, yogurt maker, warmer. 6 quart.",
        "price": {"amount": 89.95, "currency": "USD"},
        "category": "home",
        "brand": "Instant Pot",
        "merchant": "HomeEssentials",
        "in_stock": True,
        "attributes": {"capacity": "6 Quart", "color": "Stainless Steel"},
    },
    {
        "id": "prod-008",
        "title": "Dyson V15 Detect Cordless Vacuum",
        "description": "Laser reveals microscopic dust. Piezo sensor counts and sizes particles. Up to 60 min runtime.",
        "price": {"amount": 749.99, "currency": "USD"},
        "category": "home",
        "brand": "Dyson",
        "merchant": "HomeEssentials",
        "in_stock": True,
        "attributes": {"type": "Cordless Stick", "runtime": "60 minutes"},
    },
    {
        "id": "prod-009",
        "title": "Kindle Paperwhite (16 GB)",
        "description": "6.8-inch display with adjustable warm light. Waterproof. Weeks of battery life. Purpose-built for reading.",
        "price": {"amount": 149.99, "currency": "USD"},
        "category": "electronics",
        "brand": "Amazon",
        "merchant": "TechStore",
        "in_stock": True,
        "attributes": {"storage": "16GB", "display": "6.8-inch"},
    },
    {
        "id": "prod-010",
        "title": "YETI Rambler 20 oz Tumbler",
        "description": "Double-wall vacuum insulated. Keeps drinks hot or cold. MagSlider lid. Dishwasher safe.",
        "price": {"amount": 35.00, "currency": "USD"},
        "category": "home",
        "brand": "YETI",
        "merchant": "HomeEssentials",
        "in_stock": True,
        "attributes": {"capacity": "20 oz", "color": "Navy"},
    },
    {
        "id": "prod-011",
        "title": "Adidas Ultraboost 5 Running Shoes",
        "description": "Premium running shoes with BOOST midsole for energy return. Primeknit+ upper for adaptive fit.",
        "price": {"amount": 190.00, "currency": "USD"},
        "category": "clothing",
        "brand": "Adidas",
        "merchant": "SportsFit",
        "in_stock": True,
        "attributes": {"color": "Core Black", "sizes": "6-14"},
    },
    {
        "id": "prod-012",
        "title": "KitchenAid Artisan Stand Mixer",
        "description": "5-quart stainless steel bowl. 10 speeds. Tilt-head design. Includes flat beater, dough hook, wire whip.",
        "price": {"amount": 449.99, "currency": "USD"},
        "category": "home",
        "brand": "KitchenAid",
        "merchant": "HomeEssentials",
        "in_stock": True,
        "attributes": {"capacity": "5 Quart", "color": "Empire Red"},
    },
    {
        "id": "prod-013",
        "title": "Ray-Ban Wayfarer Classic Sunglasses",
        "description": "Iconic design with polarized G-15 lenses. Acetate frame. UV protection.",
        "price": {"amount": 163.00, "currency": "USD"},
        "category": "clothing",
        "brand": "Ray-Ban",
        "merchant": "FashionHub",
        "in_stock": True,
        "attributes": {"lens": "Polarized G-15", "frame": "Black Acetate"},
    },
    {
        "id": "prod-014",
        "title": "Bose SoundLink Flex Bluetooth Speaker",
        "description": "Portable waterproof speaker with deep, clear sound. 12-hour battery life. IP67 rated.",
        "price": {"amount": 149.00, "currency": "USD"},
        "category": "electronics",
        "brand": "Bose",
        "merchant": "TechStore",
        "in_stock": True,
        "attributes": {"waterproof": "IP67", "battery": "12 hours"},
    },
    {
        "id": "prod-015",
        "title": "Nespresso Vertuo Next Coffee Machine",
        "description": "Centrifusion brewing for coffee and espresso. One-touch operation. 5 cup sizes.",
        "price": {"amount": 179.00, "currency": "USD"},
        "category": "home",
        "brand": "Nespresso",
        "merchant": "HomeEssentials",
        "in_stock": True,
        "attributes": {"color": "Matte Black", "type": "Capsule"},
    },
]

# In-memory state
_checkout_sessions: dict[str, dict] = {}
_orders: dict[str, dict] = {}
_carts: dict[str, list[dict]] = {"default": []}


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------
class CartItemRequest(BaseModel):
    product_id: str
    quantity: int = 1


class ShippingAddressRequest(BaseModel):
    name: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"


class CheckoutUpdateRequest(BaseModel):
    shipping_address: ShippingAddressRequest | None = None


# ---------------------------------------------------------------------------
# Product Discovery endpoints
# ---------------------------------------------------------------------------
@app.get("/ucp/v1/products/search")
def search_products(
    q: str = Query("", description="Search query"),
    category: str = Query("", description="Filter by category"),
    min_price: float = Query(0, description="Minimum price"),
    max_price: float = Query(0, description="Maximum price"),
    limit: int = Query(10, description="Max results"),
):
    results = PRODUCTS

    if q:
        q_lower = q.lower()
        results = [
            p
            for p in results
            if q_lower in p["title"].lower()
            or q_lower in p["description"].lower()
            or q_lower in p.get("brand", "").lower()
            or q_lower in p.get("category", "").lower()
        ]

    if category:
        cat_lower = category.lower()
        results = [p for p in results if p.get("category", "").lower() == cat_lower]

    if min_price > 0:
        results = [p for p in results if p["price"]["amount"] >= min_price]

    if max_price > 0:
        results = [p for p in results if p["price"]["amount"] <= max_price]

    return {"products": results[:limit], "total": len(results)}


@app.get("/ucp/v1/products/{product_id}")
def get_product(product_id: str):
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Product not found")


# ---------------------------------------------------------------------------
# Cart endpoints
# ---------------------------------------------------------------------------
@app.get("/ucp/v1/cart")
def get_cart():
    cart_items = _carts.get("default", [])
    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    tax = round(subtotal * 0.08, 2)
    shipping = 0.0 if subtotal >= 50 else 5.99
    return {
        "items": cart_items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "total": round(subtotal + tax + shipping, 2),
    }


@app.post("/ucp/v1/cart/items")
def add_to_cart(item: CartItemRequest):
    product = None
    for p in PRODUCTS:
        if p["id"] == item.product_id:
            product = p
            break
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cart = _carts.setdefault("default", [])

    for cart_item in cart:
        if cart_item["product_id"] == item.product_id:
            cart_item["quantity"] += item.quantity
            return {"message": "Cart updated", "cart": get_cart()}

    cart.append(
        {
            "product_id": product["id"],
            "title": product["title"],
            "price": product["price"]["amount"],
            "quantity": item.quantity,
        }
    )
    return {"message": "Item added to cart", "cart": get_cart()}


@app.delete("/ucp/v1/cart/items/{product_id}")
def remove_from_cart(product_id: str):
    cart = _carts.get("default", [])
    for i, item in enumerate(cart):
        if item["product_id"] == product_id:
            cart.pop(i)
            return {"message": "Item removed", "cart": get_cart()}
    raise HTTPException(status_code=404, detail="Item not in cart")


# ---------------------------------------------------------------------------
# Checkout endpoints (UCP session create / update / complete)
# ---------------------------------------------------------------------------
@app.post("/ucp/v1/checkout/sessions")
def create_checkout_session():
    cart = _carts.get("default", [])
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    subtotal = sum(item["price"] * item["quantity"] for item in cart)
    tax = round(subtotal * 0.08, 2)
    shipping = 0.0 if subtotal >= 50 else 5.99

    session_id = f"ses-{uuid.uuid4().hex[:12]}"
    session = {
        "session_id": session_id,
        "status": "created",
        "cart_summary": [
            {
                "title": item["title"],
                "quantity": item["quantity"],
                "price": item["price"],
            }
            for item in cart
        ],
        "subtotal": subtotal,
        "tax": tax,
        "shipping_cost": shipping,
        "total": round(subtotal + tax + shipping, 2),
        "shipping_address": None,
    }
    _checkout_sessions[session_id] = session
    return session


@app.patch("/ucp/v1/checkout/sessions/{session_id}")
def update_checkout_session(session_id: str, update: CheckoutUpdateRequest):
    session = _checkout_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if update.shipping_address:
        session["shipping_address"] = update.shipping_address.model_dump()
        session["status"] = "shipping_set"

    return session


@app.post("/ucp/v1/checkout/sessions/{session_id}/complete")
def complete_checkout(session_id: str):
    session = _checkout_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.get("shipping_address"):
        raise HTTPException(
            status_code=400, detail="Shipping address is required before completing"
        )

    order_id = f"ord-{uuid.uuid4().hex[:12]}"
    delivery_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")

    order = {
        "order_id": order_id,
        "status": "processing",
        "items": session["cart_summary"],
        "total": session["total"],
        "shipping_address": session["shipping_address"],
        "tracking_number": f"TRK{uuid.uuid4().hex[:10].upper()}",
        "estimated_delivery": delivery_date,
    }
    _orders[order_id] = order

    session["status"] = "completed"
    _carts["default"] = []

    return order


# ---------------------------------------------------------------------------
# Order management
# ---------------------------------------------------------------------------
@app.get("/ucp/v1/orders/{order_id}")
def get_order(order_id: str):
    order = _orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.get("/ucp/v1/orders")
def list_orders():
    return {"orders": list(_orders.values())}


def run():
    """Entry point for the mock server."""
    import uvicorn

    print("Starting Mock UCP Server on http://localhost:8000")
    print("Endpoints:")
    print("  GET  /ucp/v1/products/search?q=...&category=...&min_price=...&max_price=...")
    print("  GET  /ucp/v1/products/{product_id}")
    print("  GET  /ucp/v1/cart")
    print("  POST /ucp/v1/cart/items")
    print("  DELETE /ucp/v1/cart/items/{product_id}")
    print("  POST /ucp/v1/checkout/sessions")
    print("  PATCH /ucp/v1/checkout/sessions/{session_id}")
    print("  POST /ucp/v1/checkout/sessions/{session_id}/complete")
    print("  GET  /ucp/v1/orders/{order_id}")
    print("  GET  /ucp/v1/orders")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
