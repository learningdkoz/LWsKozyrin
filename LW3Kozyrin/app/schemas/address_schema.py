from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class AddressCreate(BaseModel):
    """Схема для создания адреса"""
    street: str = Field(..., min_length=1, max_length=200, description="Улица")
    city: str = Field(..., min_length=1, max_length=100, description="Город")
    state: Optional[str] = Field(None, max_length=100, description="Регион/область")
    zip_code: str = Field(..., min_length=5, max_length=20, description="Почтовый индекс")
    country: str = Field(default="Russia", max_length=100, description="Страна")
    user_id: int = Field(..., gt=0, description="ID пользователя")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "street": "ул. Ленина, д. 10",
                "city": "Москва",
                "state": "Московская область",
                "zip_code": "123456",
                "country": "Russia",
                "user_id": 1
            }
        }
    )


class AddressUpdate(BaseModel):
    """Схема для обновления адреса"""
    street: Optional[str] = Field(None, min_length=1, max_length=200)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, min_length=5, max_length=20)
    country: Optional[str] = Field(None, max_length=100)


class AddressResponse(BaseModel):
    """Схема для ответа с данными адреса"""
    id: int
    street: str
    city: str
    state: Optional[str]
    zip_code: str
    country: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)
