"""Shopping tools for Claude's tool-use.

Defines the tool schemas and execution logic that the Claude agent uses
to interact with UCP endpoints via the UCPClient.
"""

from __future__ import annotations

import json
from typing import Any

from .ucp_client import UCPClient

# ---------------------------------------------------------------------------
# Tool definitions (Claude tool-use JSON schemas)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_products",
        "description": (
            "Search for products available for purchase. "
            "Use this to find products matching the user's request. "
            "You can search by keyword, filter by category (electronics, clothing, home), "
            "and set price range filters."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'headphones', 'running shoes', 'coffee')",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category: electronics, clothing, or home",
                    "enum": ["electronics", "clothing", "home", ""],
                },
                "min_price": {
                    "type": "number",
                    "description": "Minimum price filter",
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price filter",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_product_details",
        "description": (
            "Get full details for a specific product by its ID. "
            "Use this after searching to show the user more information about a product."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The product ID (e.g., 'prod-001')",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "add_to_cart",
        "description": (
            "Add a product to the shopping cart. "
            "Use this when the user wants to buy a product or add it to their cart."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The product ID to add",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of items to add (default: 1)",
                    "default": 1,
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "view_cart",
        "description": (
            "View the current shopping cart contents, including items, quantities, and totals. "
            "Use this when the user asks to see their cart."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "remove_from_cart",
        "description": "Remove a product from the shopping cart.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "The product ID to remove",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "checkout",
        "description": (
            "Start the checkout process. Creates a UCP checkout session. "
            "Use this when the user wants to proceed to purchase."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "set_shipping_address",
        "description": (
            "Set the shipping address for the current checkout session. "
            "Use this during checkout when the user provides their delivery address."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The checkout session ID",
                },
                "name": {
                    "type": "string",
                    "description": "Recipient's full name",
                },
                "street": {
                    "type": "string",
                    "description": "Street address",
                },
                "city": {
                    "type": "string",
                    "description": "City",
                },
                "state": {
                    "type": "string",
                    "description": "State/province code (e.g., 'CA')",
                },
                "zip_code": {
                    "type": "string",
                    "description": "ZIP/postal code",
                },
                "country": {
                    "type": "string",
                    "description": "Country code (default: 'US')",
                    "default": "US",
                },
            },
            "required": ["session_id", "name", "street", "city", "state", "zip_code"],
        },
    },
    {
        "name": "confirm_order",
        "description": (
            "Confirm and place the order. Completes the UCP checkout session. "
            "Use this after shipping address is set and the user confirms they want to place the order."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The checkout session ID to complete",
                },
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "check_order_status",
        "description": "Check the status of a placed order, including tracking information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to check",
                },
            },
            "required": ["order_id"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------

async def execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    ucp_client: UCPClient,
) -> str:
    """Execute a shopping tool and return the result as a JSON string."""
    try:
        if tool_name == "search_products":
            products = await ucp_client.search_products(
                query=tool_input.get("query", ""),
                category=tool_input.get("category", ""),
                min_price=tool_input.get("min_price", 0),
                max_price=tool_input.get("max_price", 0),
            )
            if not products:
                return json.dumps({"message": "No products found matching your search.", "products": []})
            return json.dumps(
                {
                    "products": [
                        {
                            "id": p.id,
                            "title": p.title,
                            "price": str(p.price),
                            "brand": p.brand,
                            "category": p.category,
                            "in_stock": p.in_stock,
                        }
                        for p in products
                    ],
                    "total": len(products),
                }
            )

        elif tool_name == "get_product_details":
            product = await ucp_client.get_product(tool_input["product_id"])
            return json.dumps(
                {
                    "id": product.id,
                    "title": product.title,
                    "description": product.description,
                    "price": str(product.price),
                    "brand": product.brand,
                    "category": product.category,
                    "merchant": product.merchant,
                    "in_stock": product.in_stock,
                    "attributes": product.attributes,
                }
            )

        elif tool_name == "add_to_cart":
            result = await ucp_client.add_to_cart(
                product_id=tool_input["product_id"],
                quantity=tool_input.get("quantity", 1),
            )
            return json.dumps(result)

        elif tool_name == "view_cart":
            cart = await ucp_client.get_cart()
            return json.dumps(cart)

        elif tool_name == "remove_from_cart":
            result = await ucp_client.remove_from_cart(tool_input["product_id"])
            return json.dumps(result)

        elif tool_name == "checkout":
            session = await ucp_client.create_checkout_session()
            return json.dumps(session.model_dump())

        elif tool_name == "set_shipping_address":
            address = {
                "name": tool_input["name"],
                "street": tool_input["street"],
                "city": tool_input["city"],
                "state": tool_input["state"],
                "zip_code": tool_input["zip_code"],
                "country": tool_input.get("country", "US"),
            }
            session = await ucp_client.update_checkout_session(
                session_id=tool_input["session_id"],
                shipping_address=address,
            )
            return json.dumps(session.model_dump())

        elif tool_name == "confirm_order":
            order = await ucp_client.complete_checkout(tool_input["session_id"])
            return json.dumps(order.model_dump())

        elif tool_name == "check_order_status":
            order = await ucp_client.get_order(tool_input["order_id"])
            return json.dumps(order.model_dump())

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except Exception as e:
        return json.dumps({"error": str(e)})
