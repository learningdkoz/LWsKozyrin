from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.order import OrderStatus

class OrderItemCreate(BaseModel):
    """Схема для создания элемента заказа"""
    product_id: int = Field(..., gt=0, description="ID продукта")
    quantity: int = Field(..., gt=0, description="Количество")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
                "quantity": 2
            }
        }
    )


class OrderItemResponse(BaseModel):
    """Схема для ответа с данными элемента заказа"""
    id: int
    product_id: int
    quantity: int
    price_at_purchase: float

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """Схема для создания заказа"""
    user_id: int = Field(..., gt=0, description="ID пользователя")
    address_id: int = Field(..., gt=0, description="ID адреса доставки")
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Список товаров в заказе")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 2, "quantity": 1}
                ]
            }
        }
    )


class OrderUpdate(BaseModel):
    """Схема для обновления заказа"""
    address_id: Optional[int] = Field(None, gt=0)
    status: Optional[OrderStatus] = None


class OrderResponse(BaseModel):
    """Схема для ответа с данными заказа"""
    id: int
    user_id: int
    address_id: int
    status: OrderStatus
    total_price: float
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Схема для ответа со списком заказов"""
    orders: list[OrderResponse]
    total_count: int = Field(..., description="Общее количество заказов")
