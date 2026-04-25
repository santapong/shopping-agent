// Shopping Agent web demo — vanilla JS, talks to UCP routes + /api/chat.

const $ = (sel) => document.querySelector(sel);

const api = {
  async health() {
    const r = await fetch("/api/health");
    if (!r.ok) throw new Error(`Health failed: ${r.status}`);
    return r.json();
  },
  async searchProducts({ q = "", category = "" } = {}) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (category) params.set("category", category);
    const r = await fetch(`/ucp/v1/products/search?${params}`);
    if (!r.ok) throw new Error(`Search failed: ${r.status}`);
    return r.json();
  },
  async getCart() {
    const r = await fetch("/ucp/v1/cart");
    if (!r.ok) throw new Error(`Cart failed: ${r.status}`);
    return r.json();
  },
  async addToCart(productId, quantity = 1) {
    const r = await fetch("/ucp/v1/cart/items", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_id: productId, quantity }),
    });
    if (!r.ok) throw new Error(`Add failed: ${r.status}`);
    return r.json();
  },
  async removeFromCart(productId) {
    const r = await fetch(`/ucp/v1/cart/items/${productId}`, { method: "DELETE" });
    if (!r.ok) throw new Error(`Remove failed: ${r.status}`);
    return r.json();
  },
  async createCheckout() {
    const r = await fetch("/ucp/v1/checkout/sessions", { method: "POST" });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `Checkout create failed: ${r.status}`);
    }
    return r.json();
  },
  async setShipping(sessionId, address) {
    const r = await fetch(`/ucp/v1/checkout/sessions/${sessionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ shipping_address: address }),
    });
    if (!r.ok) throw new Error(`Shipping failed: ${r.status}`);
    return r.json();
  },
  async completeCheckout(sessionId) {
    const r = await fetch(`/ucp/v1/checkout/sessions/${sessionId}/complete`, {
      method: "POST",
    });
    if (!r.ok) throw new Error(`Complete failed: ${r.status}`);
    return r.json();
  },
  async chat(message) {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || `Chat failed: ${r.status}`);
    return data;
  },
  async resetChat() {
    const r = await fetch("/api/chat/reset", { method: "POST" });
    if (!r.ok) throw new Error(`Reset failed: ${r.status}`);
    return r.json();
  },
};

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function toast(msg, kind = "info") {
  const t = $("#toast");
  t.textContent = msg;
  t.className = `toast ${kind}`;
  t.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), 2400);
}

// ---------------------------------------------------------------------------
// Health check / "Run Demo" button
// ---------------------------------------------------------------------------
async function runDemo() {
  const pill = $("#health-status");
  pill.className = "status-pill checking";
  pill.textContent = "checking…";
  try {
    const h = await api.health();
    pill.className = "status-pill ok";
    pill.textContent = `UCP online · ${h.products} products`;
    await loadProducts();
    await refreshCart();
    toast("Demo ready — UCP server is responding.", "success");
  } catch (e) {
    pill.className = "status-pill fail";
    pill.textContent = "offline";
    toast(`Health check failed: ${e.message}`, "error");
  }
}

// ---------------------------------------------------------------------------
// Products
// ---------------------------------------------------------------------------
function formatPrice(price) {
  const symbols = { USD: "$", EUR: "€", GBP: "£", JPY: "¥", THB: "฿" };
  const sym = symbols[price.currency] || price.currency + " ";
  return `${sym}${price.amount.toFixed(2)}`;
}

function renderProducts(products) {
  const grid = $("#products-grid");
  if (!products.length) {
    grid.innerHTML = `<p class="empty">No products match your search.</p>`;
    return;
  }
  grid.innerHTML = products
    .map(
      (p) => `
      <div class="product-card" data-id="${p.id}">
        <div class="title">${escapeHtml(p.title)}</div>
        <div class="meta">
          <span class="badge">${escapeHtml(p.category)}</span>
          <span>${escapeHtml(p.brand)}</span>
        </div>
        <div class="price">${formatPrice(p.price)}</div>
        <button class="add-btn primary" data-id="${p.id}">Add to Cart</button>
      </div>`,
    )
    .join("");
  grid.querySelectorAll(".add-btn").forEach((btn) =>
    btn.addEventListener("click", () => addToCart(btn.dataset.id)),
  );
}

async function loadProducts() {
  const q = $("#search-input").value.trim();
  const category = $("#category-select").value;
  try {
    const data = await api.searchProducts({ q, category });
    renderProducts(data.products || []);
  } catch (e) {
    toast(e.message, "error");
  }
}

async function addToCart(productId) {
  try {
    await api.addToCart(productId, 1);
    toast("Added to cart.", "success");
    await refreshCart();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Cart
// ---------------------------------------------------------------------------
function renderCart(cart) {
  const list = $("#cart-items");
  const totals = $("#cart-totals");
  const checkoutBtn = $("#checkout-btn");

  if (!cart.items || !cart.items.length) {
    list.innerHTML = `<p class="empty">Your cart is empty.</p>`;
    totals.classList.add("hidden");
    checkoutBtn.disabled = true;
    return;
  }

  list.innerHTML = cart.items
    .map(
      (item) => `
      <div class="cart-item">
        <div class="info">
          <div class="title">${escapeHtml(item.title)}</div>
          <div class="qty">Qty ${item.quantity} × $${item.price.toFixed(2)}</div>
        </div>
        <div class="price">$${(item.price * item.quantity).toFixed(2)}</div>
        <button class="remove" data-id="${item.product_id}" title="Remove">✕</button>
      </div>`,
    )
    .join("");

  list.querySelectorAll(".remove").forEach((btn) =>
    btn.addEventListener("click", () => removeFromCart(btn.dataset.id)),
  );

  $("#cart-subtotal").textContent = `$${cart.subtotal.toFixed(2)}`;
  $("#cart-tax").textContent = `$${cart.tax.toFixed(2)}`;
  $("#cart-shipping").textContent = `$${cart.shipping.toFixed(2)}`;
  $("#cart-total").textContent = `$${cart.total.toFixed(2)}`;
  totals.classList.remove("hidden");
  checkoutBtn.disabled = false;
}

async function refreshCart() {
  try {
    const cart = await api.getCart();
    renderCart(cart);
  } catch (e) {
    toast(e.message, "error");
  }
}

async function removeFromCart(productId) {
  try {
    await api.removeFromCart(productId);
    toast("Removed.", "info");
    await refreshCart();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Checkout
// ---------------------------------------------------------------------------
let activeSessionId = null;

async function openCheckout() {
  try {
    const session = await api.createCheckout();
    activeSessionId = session.session_id;
    $("#checkout-result").classList.add("hidden");
    $("#checkout-form").reset();
    $("#checkout-form").querySelector('input[name="country"]').value = "US";
    $("#checkout-modal").classList.remove("hidden");
  } catch (e) {
    toast(e.message, "error");
  }
}

async function handleCheckoutSubmit(e) {
  e.preventDefault();
  if (!activeSessionId) return;
  const form = e.target;
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    await api.setShipping(activeSessionId, data);
    const order = await api.completeCheckout(activeSessionId);
    const result = $("#checkout-result");
    result.innerHTML = `
      <strong>Order placed!</strong><br />
      Status: ${escapeHtml(order.status)} &middot; ETA: ${escapeHtml(order.estimated_delivery)}
      <code>Order: ${escapeHtml(order.order_id)}</code>
      <code>Tracking: ${escapeHtml(order.tracking_number)}</code>
    `;
    result.classList.remove("hidden");
    activeSessionId = null;
    await refreshCart();
    toast("Order placed.", "success");
  } catch (e) {
    toast(e.message, "error");
  }
}

function closeCheckout() {
  $("#checkout-modal").classList.add("hidden");
  activeSessionId = null;
}

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------
function appendMessage(role, text) {
  const box = $("#chat-messages");
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

async function handleChatSubmit(e) {
  e.preventDefault();
  const input = $("#chat-input");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  appendMessage("user", message);
  const thinking = appendMessage("thinking", "Agent is thinking…");
  try {
    const { reply } = await api.chat(message);
    thinking.remove();
    appendMessage("agent", reply);
    // The agent likely changed the cart; refresh.
    await refreshCart();
  } catch (e) {
    thinking.remove();
    appendMessage("error", e.message);
  }
}

async function resetChat() {
  try {
    await api.resetChat();
    $("#chat-messages").innerHTML = `
      <div class="msg agent">Conversation reset. What would you like to shop for?</div>`;
    toast("Chat cleared.", "info");
  } catch (e) {
    toast(e.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function escapeHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ---------------------------------------------------------------------------
// Wire up
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  $("#run-demo-btn").addEventListener("click", runDemo);
  $("#search-btn").addEventListener("click", loadProducts);
  $("#search-input").addEventListener("keydown", (e) => {
    if (e.key === "Enter") loadProducts();
  });
  $("#category-select").addEventListener("change", loadProducts);
  $("#refresh-cart-btn").addEventListener("click", refreshCart);
  $("#checkout-btn").addEventListener("click", openCheckout);
  $("#close-modal-btn").addEventListener("click", closeCheckout);
  $("#checkout-form").addEventListener("submit", handleCheckoutSubmit);
  $("#chat-form").addEventListener("submit", handleChatSubmit);
  $("#reset-chat-btn").addEventListener("click", resetChat);

  // Initial load — show the catalog right away so users see something.
  loadProducts();
  refreshCart();
});
