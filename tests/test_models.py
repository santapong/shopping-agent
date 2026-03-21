"""Tests for data models."""

from shopping_agent.models import Cart, CartItem, Money, Product, Currency


def _make_product(id: str = "prod-001", price: float = 100.0) -> Product:
    return Product(
        id=id,
        title="Test Product",
        description="A test product",
        price=Money(amount=price, currency=Currency.USD),
        category="electronics",
        brand="TestBrand",
        merchant="TestStore",
    )


def test_money_str():
    m = Money(amount=29.99, currency=Currency.USD)
    assert str(m) == "$29.99"

    m_eur = Money(amount=19.50, currency=Currency.EUR)
    assert str(m_eur) == "€19.50"


def test_cart_add_item():
    cart = Cart()
    product = _make_product()
    cart.add_item(product, quantity=2)

    assert len(cart.items) == 1
    assert cart.items[0].quantity == 2
    assert cart.items[0].item_total.amount == 200.0


def test_cart_add_same_product_increases_quantity():
    cart = Cart()
    product = _make_product()
    cart.add_item(product, quantity=1)
    cart.add_item(product, quantity=3)

    assert len(cart.items) == 1
    assert cart.items[0].quantity == 4


def test_cart_remove_item():
    cart = Cart()
    product = _make_product()
    cart.add_item(product)

    assert cart.remove_item("prod-001") is True
    assert len(cart.items) == 0
    assert cart.remove_item("nonexistent") is False


def test_cart_totals():
    cart = Cart()
    cart.add_item(_make_product("p1", 30.0), quantity=1)
    cart.add_item(_make_product("p2", 25.0), quantity=2)

    assert cart.subtotal == 80.0
    assert cart.tax == 6.40  # 8%
    assert cart.shipping == 0.0  # free over $50
    assert cart.total == 86.40


def test_cart_shipping_under_50():
    cart = Cart()
    cart.add_item(_make_product("p1", 20.0), quantity=1)

    assert cart.subtotal == 20.0
    assert cart.shipping == 5.99


def test_cart_clear():
    cart = Cart()
    cart.add_item(_make_product())
    cart.clear()
    assert len(cart.items) == 0
