"""Схемы для сообщений RabbitMQ"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.order import OrderStatus


class ProductMessage(BaseModel):
    """Схема сообщения для создания/обновления продукта"""
    action: str = Field(..., description="Действие: create, update, mark_out_of_stock")
    id: Optional[int] = Field(None, description="ID продукта (для update)")
    name: Optional[str] = Field(None, description="Название продукта")
    price: Optional[float] = Field(None, gt=0, description="Цена продукта")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Количество на складе")

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "action": "create",
                "name": "Ноутбук ASUS",
                "price": 75000.0,
                "stock_quantity": 10
            },
            {
                "action": "update",
                "id": 1,
                "stock_quantity": 5
            },
            {
                "action": "mark_out_of_stock",
                "id": 1
            }
        ]
    }}


class OrderItemMessage(BaseModel):
    """Элемент заказа в сообщении"""
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderMessage(BaseModel):
    """Схема сообщения для создания/обновления заказа"""
    action: str = Field(..., description="Действие: create, update_status")
    id: Optional[int] = Field(None, description="ID заказа (для update_status)")
    user_id: Optional[int] = Field(None, gt=0)
    address_id: Optional[int] = Field(None, gt=0)
    items: Optional[List[OrderItemMessage]] = Field(None, description="Список товаров")
    status: Optional[OrderStatus] = Field(None, description="Новый статус заказа")

    model_config = {"json_schema_extra": {
        "examples": [
            {
                "action": "create",
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 1, "quantity": 2},
                    {"product_id": 2, "quantity": 1}
                ]
            },
            {
                "action": "update_status",
                "id": 1,
                "status": "processing"
            }
        ]
    }}
