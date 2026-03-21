"""Data models for UCP shopping agent."""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    THB = "THB"


class Money(BaseModel):
    amount: float
    currency: Currency = Currency.USD

    def __str__(self) -> str:
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "THB": "฿"}
        symbol = symbols.get(self.currency.value, self.currency.value)
        return f"{symbol}{self.amount:.2f}"


class Product(BaseModel):
    id: str
    title: str
    description: str
    price: Money
    category: str = ""
    brand: str = ""
    image_url: str = ""
    merchant: str = ""
    in_stock: bool = True
    attributes: dict[str, str] = Field(default_factory=dict)


class CartItem(BaseModel):
    product: Product
    quantity: int = 1

    @property
    def item_total(self) -> Money:
        return Money(
            amount=self.product.price.amount * self.quantity,
            currency=self.product.price.currency,
        )


class Cart(BaseModel):
    items: list[CartItem] = Field(default_factory=list)

    @property
    def subtotal(self) -> float:
        return sum(item.item_total.amount for item in self.items)

    @property
    def tax(self) -> float:
        return round(self.subtotal * 0.08, 2)

    @property
    def shipping(self) -> float:
        if self.subtotal >= 50:
            return 0.0
        return 5.99

    @property
    def total(self) -> float:
        return round(self.subtotal + self.tax + self.shipping, 2)

    def add_item(self, product: Product, quantity: int = 1) -> None:
        for item in self.items:
            if item.product.id == product.id:
                item.quantity += quantity
                return
        self.items.append(CartItem(product=product, quantity=quantity))

    def remove_item(self, product_id: str) -> bool:
        for i, item in enumerate(self.items):
            if item.product.id == product_id:
                self.items.pop(i)
                return True
        return False

    def clear(self) -> None:
        self.items.clear()


class ShippingAddress(BaseModel):
    name: str
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"


class CheckoutSessionStatus(str, Enum):
    CREATED = "created"
    SHIPPING_SET = "shipping_set"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CheckoutSession(BaseModel):
    session_id: str
    status: CheckoutSessionStatus = CheckoutSessionStatus.CREATED
    cart_summary: list[dict] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    shipping_cost: float = 0.0
    total: float = 0.0
    shipping_address: ShippingAddress | None = None


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(BaseModel):
    order_id: str
    status: OrderStatus = OrderStatus.PENDING
    items: list[dict] = Field(default_factory=list)
    total: float = 0.0
    shipping_address: ShippingAddress | None = None
    tracking_number: str = ""
    estimated_delivery: str = ""
