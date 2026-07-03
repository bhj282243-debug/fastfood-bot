import re
from enum import Enum
from pydantic import BaseModel, field_validator
from typing import List, Optional, Any


# ──────────────────────────────────────────────
#  Аутентификация
# ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ──────────────────────────────────────────────
#  Статусы заказа — только допустимые значения
# ──────────────────────────────────────────────
class OrderStatus(str, Enum):
    new = "new"
    accepted = "accepted"
    preparing = "preparing"
    ready = "ready"
    delivering = "delivering"
    completed = "completed"
    cancelled = "cancelled"


# ──────────────────────────────────────────────
#  Меню
# ──────────────────────────────────────────────
class ProductOptionBase(BaseModel):
    name: str
    price: float


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    weight: Optional[str] = None
    category_id: int
    is_available: bool = True


class ProductCreate(ProductBase):
    options: List[ProductOptionBase] = []


class Product(ProductBase):
    id: int
    is_popular: bool = False
    options: List[ProductOptionBase] = []

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    products: List[Product] = []

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────
#  Заказы
# ──────────────────────────────────────────────
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    options: Optional[str] = None


class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    address: Optional[str] = None
    delivery_type: str = "delivery"
    delivery_price: float = 0
    discount: float = 0
    payment_method: str = "cash"
    comment: Optional[str] = None
    items: List[OrderItemCreate]

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        # Убираем пробелы, дефисы, скобки
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        # Узбекские номера: +998XXXXXXXXX или 998XXXXXXXXX или 8 цифр (локальный)
        if not re.match(r"^(\+?998)?\d{7,9}$", cleaned):
            raise ValueError("Некорректный номер телефона")
        return cleaned

    @field_validator("delivery_price")
    @classmethod
    def validate_delivery_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Стоимость доставки не может быть отрицательной")
        return v

    @field_validator("discount")
    @classmethod
    def validate_discount(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Скидка не может быть отрицательной")
        return v


class ProductShort(BaseModel):
    id: int
    name: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class OrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    options: Optional[str] = None
    product: Optional[ProductShort] = None

    class Config:
        from_attributes = True


class Order(BaseModel):
    id: int
    customer_name: str
    phone: str
    address: Optional[str] = None
    delivery_type: str
    delivery_price: float
    discount: float
    payment_method: str
    comment: Optional[str] = None
    status: str
    total_price: float
    created_at: Optional[Any] = None
    items: List[OrderItem] = []

    class Config:
        from_attributes = True


class OrderUpdateStatus(BaseModel):
    status: OrderStatus  # только допустимые статусы
