# Google UCP for Shopping — Architecture & Ordering Guide

This document explains how this project uses **Google's Universal Commerce
Protocol (UCP)** to let an AI agent shop on a user's behalf, where the
boundaries of UCP lie, and exactly which tools fire in what order to take a
parcel from "find me headphones" to "shipped".

> The reference implementation lives in `src/shopping_agent/`. Wherever this
> guide cites a tool, endpoint, or model, you can open the file and follow the
> code path end-to-end.

---

## 1. What UCP is (and is not)

UCP is an open, REST-style protocol for **agentic commerce**: a uniform shape
for product discovery, cart, checkout-session, and order endpoints so that any
AI agent can transact with any UCP-compliant merchant without bespoke
integrations.

UCP standardises the *interface*. It does **not** ship:

- a product catalog,
- a payment processor,
- merchant-side fulfillment, or
- the LLM that decides what to buy.

Those are plugged in around UCP. In this repo:

| UCP role           | This project's implementation                              |
| ------------------ | ---------------------------------------------------------- |
| UCP server         | `src/shopping_agent/mock_server.py` (FastAPI, in-memory)   |
| UCP client (SDK)   | `src/shopping_agent/ucp_client.py` (httpx)                 |
| Shopping agent     | `src/shopping_agent/agent.py` (Claude tool-use loop)       |
| Tool surface       | `src/shopping_agent/tools.py` (9 tools the LLM can call)   |

---

## 2. Architecture

```
┌──────────────┐    text     ┌────────────────────────┐    tool_use    ┌───────────────────┐
│              │────────────▶│                        │───────────────▶│                   │
│  User (CLI)  │             │  Claude Shopping Agent │                │   Shopping Tools  │
│  main.py     │◀────────────│  agent.py              │◀───────────────│   tools.py        │
│              │  reply      │  (system prompt +      │  tool_result   │  (9 UCP-backed    │
└──────────────┘             │   agentic loop)        │                │   functions)      │
                             └────────────────────────┘                └─────────┬─────────┘
                                                                                 │ httpx
                                                                                 ▼
                                                                       ┌───────────────────┐
                                                                       │   UCP Client      │
                                                                       │   ucp_client.py   │
                                                                       └─────────┬─────────┘
                                                                                 │ HTTP
                                                                                 ▼
                                                       ┌──────────────────────────────────────┐
                                                       │   UCP Server  (mock_server.py)       │
                                                       │   /ucp/v1/products/*                 │
                                                       │   /ucp/v1/cart/*                     │
                                                       │   /ucp/v1/checkout/sessions/*        │
                                                       │   /ucp/v1/orders/*                   │
                                                       └─────────┬────────────────────────────┘
                                                                 │
                                                                 ▼
                                                       ┌─────────────────────────────────────┐
                                                       │   Merchant systems (catalog,        │
                                                       │   inventory, payments, fulfillment) │
                                                       │   — out of scope for UCP itself     │
                                                       └─────────────────────────────────────┘
```

### Layer responsibilities

1. **CLI (`main.py`)** — captures input, prints replies, owns the loop.
2. **Agent (`agent.py`)** — sends messages to Claude with the tool catalog,
   handles the `tool_use → tool_result` cycle until `stop_reason != "tool_use"`.
3. **Tools (`tools.py`)** — the LLM-visible surface. Each tool maps 1:1 to a
   `UCPClient` method and returns a JSON string back to the model.
4. **UCP client (`ucp_client.py`)** — typed wrapper over the HTTP endpoints,
   parses responses into `Product` / `CheckoutSession` / `Order` Pydantic
   models from `models.py`.
5. **UCP server (`mock_server.py`)** — implements the protocol. In production,
   this would be the merchant's UCP gateway.

---

## 3. The 9 tools the agent can call

Defined in `src/shopping_agent/tools.py`. Group them by lifecycle phase — that
is also the order in which a typical purchase fires them.

| Phase            | Tool                  | UCP endpoint                                        |
| ---------------- | --------------------- | --------------------------------------------------- |
| Discover         | `search_products`     | `GET  /ucp/v1/products/search`                      |
| Discover         | `get_product_details` | `GET  /ucp/v1/products/{id}`                        |
| Cart             | `add_to_cart`         | `POST /ucp/v1/cart/items`                           |
| Cart             | `view_cart`           | `GET  /ucp/v1/cart`                                 |
| Cart             | `remove_from_cart`    | `DELETE /ucp/v1/cart/items/{id}`                    |
| Checkout         | `checkout`            | `POST /ucp/v1/checkout/sessions`                    |
| Checkout         | `set_shipping_address`| `PATCH /ucp/v1/checkout/sessions/{id}`              |
| Checkout         | `confirm_order`       | `POST /ucp/v1/checkout/sessions/{id}/complete`      |
| Post-purchase    | `check_order_status`  | `GET  /ucp/v1/orders/{id}`                          |

The agent's system prompt (`agent.py:15`) instructs it to drive this sequence:
"show cart → ask for shipping → confirm → place".

---

## 4. End-to-end ordering flow ("how to order a parcel")

The canonical happy path. Each arrow is one Claude turn — either a `tool_use`
the agent emits or a `tool_result` it receives.

```
USER:  "Find me wireless headphones under $300"
  │
  ▼
[Claude] ──tool_use──▶ search_products(query="wireless headphones", max_price=300)
                        │
                        └──▶ UCPClient.search_products  ──▶ GET /ucp/v1/products/search
                                                            ◀── { products: [...] }
  ◀── tool_result: list of products
[Claude] presents top matches to the user.

USER:  "Tell me more about the Sony ones"
  │
  ▼
[Claude] ──tool_use──▶ get_product_details(product_id="prod-001")
                        └──▶ GET /ucp/v1/products/prod-001
                                                            ◀── { full product }
  ◀── tool_result
[Claude] summarises specs / price / stock.

USER:  "Add them to my cart"
  │
  ▼
[Claude] ──tool_use──▶ add_to_cart(product_id="prod-001", quantity=1)
                        └──▶ POST /ucp/v1/cart/items
                                                            ◀── { cart, message }
  ◀── tool_result

USER:  "Checkout"
  │
  ▼
[Claude] ──tool_use──▶ view_cart()              # confirms contents to user
[Claude] ──tool_use──▶ checkout()               # creates UCP session
                        └──▶ POST /ucp/v1/checkout/sessions
                                                            ◀── { session_id, status: "created", total, ... }

[Claude] asks the user for a shipping address.

USER:  "Ship to John Doe, 123 Main St, San Francisco, CA 94102"
  │
  ▼
[Claude] ──tool_use──▶ set_shipping_address(session_id, name, street, city, state, zip_code)
                        └──▶ PATCH /ucp/v1/checkout/sessions/{id}
                                                            ◀── { status: "shipping_set", ... }

[Claude] shows the final total and asks for explicit confirmation
         (per the system prompt: "always confirm before placing an order").

USER:  "Yes, place it"
  │
  ▼
[Claude] ──tool_use──▶ confirm_order(session_id)
                        └──▶ POST /ucp/v1/checkout/sessions/{id}/complete
                                                            ◀── { order_id, tracking_number,
                                                                  estimated_delivery, status: "processing" }
[Claude] returns order id + tracking number to the user.

USER:  "Where's my parcel?"
  │
  ▼
[Claude] ──tool_use──▶ check_order_status(order_id)
                        └──▶ GET /ucp/v1/orders/{id}
```

### Server-side state machine for a checkout session

```
   POST /checkout/sessions          PATCH …/{id}                    POST …/{id}/complete
created ───────────────────────▶ shipping_set ──────────────────────────────────▶ completed
   ▲                                  │                                          │
   │                                  ▼                                          ▼
   │                             (re-PATCH ok)                              Order created:
   │                                                                       status = "processing"
   └─ requires non-empty cart                                                tracking_number = TRK…
      (mock_server.py:322)                                                   eta = now + 5 days
```

`complete` enforces an invariant: the session must already have a shipping
address (`mock_server.py:370`). On success the cart is cleared and the order
moves to `processing`.

---

## 5. Why this ordering matters

1. **Discovery before cart.** The agent must never hallucinate product IDs.
   The system prompt and the `search → details → add` chain ensure every cart
   item came from a real UCP response.
2. **Cart as the source of truth.** `view_cart` is called before `checkout` so
   the user sees what they're buying. The session totals are computed
   server-side at session-creation time, so the LLM cannot misquote a price.
3. **Address before complete.** The 400 returned by
   `POST …/sessions/{id}/complete` when no address is set
   (`mock_server.py:370`) is the protocol's safety net even if the agent skips
   `set_shipping_address`.
4. **Explicit user confirmation gate.** `confirm_order` is the only
   irreversible action and is wired to a separate user turn — the agent is
   instructed never to call it without affirmative consent.

---

## 6. Limitations of UCP (and of this implementation)

These are real boundaries to be aware of when extending the project or moving
beyond the mock.

### 6.1 Protocol-level limitations

- **No payment surface.** UCP does not standardise payment instruments,
  authorisation, or PSD2/SCA flows. Production deployments still need a PSP
  integration (Stripe, Adyen, Google Pay, etc.) hung off the checkout session.
- **No identity / auth model in this repo.** The mock server has a single
  shared `default` cart and no user concept. Real merchants have to layer
  OAuth, signed agent tokens, or similar on top.
- **Single-merchant cart.** Cross-merchant carts, split shipments, and
  multi-currency orders are not modelled. `Cart` and `CheckoutSession` assume
  one currency and one fulfillment plan.
- **No live inventory / pricing guarantees.** A `Product` snapshot can be
  stale by the time `confirm_order` runs; UCP itself doesn't define a
  reservation primitive, so race conditions ("just sold out") are merchant
  business logic.
- **No returns, refunds, cancellations, or partial fulfillment.** The
  `OrderStatus` enum (`models.py:119`) ends at `delivered`/`cancelled`; there
  is no `return_requested`, no refund flow, no RMA.
- **No promotions / coupons / loyalty.** `CheckoutSession` totals are
  subtotal + flat 8% tax + flat shipping (`models.py:60`,
  `mock_server.py:268`). Real tax, shipping rates, discount codes, gift cards,
  and address-based fees are out of scope.
- **No webhooks / push.** Order status is poll-only via
  `check_order_status`. There is no shipped/delivered callback.
- **No streaming agent loop.** `agent.py` runs blocking `messages.create`
  calls; long tool chains aren't streamed back to the CLI.

### 6.2 Implementation limitations specific to this repo

- **In-memory state.** `_carts`, `_checkout_sessions`, and `_orders` in
  `mock_server.py` reset on restart. No persistence layer.
- **No concurrency safety.** The mock server mutates module-level dicts
  without locking — fine for one user, unsafe under load.
- **Single hard-coded cart key (`"default"`).** No multi-tenant isolation.
- **No retries / circuit breaker on the client.** `UCPClient` raises on any
  4xx/5xx and the agent surfaces the error string to the LLM.
- **No PII handling.** Shipping addresses are logged like any other JSON.
- **Mock catalog is 15 items.** Anything outside the seeded list will return
  empty search results — the agent is instructed to suggest alternatives
  rather than fabricate.

### 6.3 LLM-side limitations to watch for

- **Tool argument drift.** Claude can occasionally emit empty-string enums
  (e.g. `category=""`) — `tools.py:217` and `ucp_client.py:35` defend by only
  forwarding non-empty / non-zero filters.
- **Forgotten session id.** `set_shipping_address` and `confirm_order` need
  the session id from the prior `checkout` response. The agent relies on
  conversation memory; if context is truncated this can fail. The server's
  404 on unknown session id is the backstop.
- **Premature confirmation.** Without the system prompt's "always confirm"
  rule, an over-eager model could call `confirm_order` immediately after
  `set_shipping_address`. The current prompt mitigates this but does not
  cryptographically prevent it — pair it with a UI confirmation in production.

---

## 7. Extending the project

Likely next steps, roughly in dependency order:

1. **Persist state.** Swap module-level dicts for SQLite/Postgres so sessions
   survive restarts.
2. **Multi-user carts.** Key carts and sessions by an authenticated user id.
3. **Payment tool.** Add `attach_payment_method` (PATCH on the session) and a
   PSP integration; gate `confirm_order` on a successful authorisation.
4. **Webhooks.** Push `order.shipped` / `order.delivered` events instead of
   polling, and surface them as agent notifications.
5. **Real merchant adapter.** Replace `mock_server.py` with a thin shim that
   translates UCP requests to a real merchant API (Shopify, BigCommerce,
   etc.).
6. **Returns flow.** Extend `OrderStatus` and add `request_return` /
   `get_return_status` tools.

---

## 8. TL;DR

- **How to use UCP for shopping:** expose its 9 endpoints as LLM tools,
  drive them in the order *search → details → add_to_cart → view_cart →
  checkout → set_shipping_address → confirm_order → check_order_status*, and
  let the agent loop on `tool_use` until done.
- **What you still own:** auth, payments, inventory truth, fulfillment,
  returns, and anything cross-merchant.
- **The parcel's journey** is a state machine on the checkout session
  (`created → shipping_set → completed`) followed by an order
  (`processing → shipped → delivered`), all reachable through the tool
  surface above.
