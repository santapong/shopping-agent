# AI Shopping Agent

An AI-powered shopping agent that uses **Google's Universal Commerce Protocol (UCP)** and **Claude AI** to shop on your behalf.

## Features

- **Product Discovery** — Search and browse products across merchants via UCP
- **Smart Recommendations** — Claude AI understands your needs and suggests products
- **Cart Management** — Add, remove, and view items in your cart
- **UCP Checkout** — Full checkout flow using UCP sessions (create → update → complete)
- **Order Tracking** — Check order status and tracking info
- **Mock Server** — Built-in mock UCP server with 15 sample products for local testing

## Architecture

```
User (CLI) → Claude AI Agent → Shopping Tools → UCP Client → UCP REST API
```

The agent uses Claude's tool-use capability to reason about shopping requests and call UCP-integrated tools for product search, cart management, and checkout.

## Quick Start

### 1. Install

```bash
pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 3. Start the Mock UCP Server

```bash
python -m shopping_agent.mock_server
```

### 4. Run the Shopping Agent (in another terminal)

```bash
python -m shopping_agent.main
```

### 5. Start Shopping!

```
You: Find me some wireless headphones
You: Tell me more about the Sony ones
You: Add them to my cart
You: Checkout
You: Ship to John Doe, 123 Main St, San Francisco, CA 94102
You: Confirm the order
```

## UCP Endpoints (Mock Server)

| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/ucp/v1/products/search` | Search products |
| GET | `/ucp/v1/products/{id}` | Get product details |
| GET | `/ucp/v1/cart` | View cart |
| POST | `/ucp/v1/cart/items` | Add to cart |
| DELETE | `/ucp/v1/cart/items/{id}` | Remove from cart |
| POST | `/ucp/v1/checkout/sessions` | Create checkout session |
| PATCH | `/ucp/v1/checkout/sessions/{id}` | Update session (shipping) |
| POST | `/ucp/v1/checkout/sessions/{id}/complete` | Complete checkout |
| GET | `/ucp/v1/orders/{id}` | Get order status |

## Running Tests

```bash
pytest
```

## Project Structure

```
src/shopping_agent/
├── main.py          # CLI entry point
├── agent.py         # Claude AI agent with tool dispatch
├── config.py        # Configuration management
├── models.py        # Data models (Product, Cart, Order)
├── ucp_client.py    # UCP REST API client
├── tools.py         # Shopping tools for Claude tool-use
└── mock_server.py   # Mock UCP server with sample data
```

## What is UCP?

[Universal Commerce Protocol (UCP)](https://ucp.dev/) is an open standard by Google for agentic commerce. It enables AI agents to discover products, manage carts, and complete purchases across merchants through a unified protocol.

## License

MIT
