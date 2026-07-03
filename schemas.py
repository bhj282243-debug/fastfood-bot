from pydantic import BaseModel
from typing import List, Optional

# Схемы для Аутентификации
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Схемы для Меню (Категории и Продукты)
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

# Схемы для Заказов
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

class OrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    options: Optional[str] = None
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
    items: List[OrderItem] = []
    class Config:
        from_attributes = True

class OrderUpdateStatus(BaseModel):
    status: str
