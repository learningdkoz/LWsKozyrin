from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class ProductCreate(BaseModel):
    """Схема для создания продукта"""
    name: str = Field(..., min_length=1, max_length=200, description="Название продукта")
    price: float = Field(..., gt=0, description="Цена продукта")
    stock_quantity: int = Field(..., ge=0, description="Количество на складе")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Ноутбук ASUS",
                "price": 75000.0,
                "stock_quantity": 10
            }
        }
    )


class ProductUpdate(BaseModel):
    """Схема для обновления продукта"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    price: Optional[float] = Field(None, gt=0)
    stock_quantity: Optional[int] = Field(None, ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Ноутбук ASUS ROG",
                "price": 85000.0,
                "stock_quantity": 5
            }
        }
    )


class ProductResponse(BaseModel):
    """Схема для ответа с данными продукта"""
    id: int
    name: str
    price: float
    stock_quantity: int

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Схема для ответа со списком продуктов"""
    products: list[ProductResponse]
    total_count: int = Field(..., description="Общее количество продуктов")
