from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class Address(Base):
    """
    Модель адреса доставки

    Attributes:
        id: Уникальный идентификатор адреса
        street: Улица
        city: Город
        state: Регион/область
        zip_code: Почтовый индекс
        country: Страна
        user_id: ID пользователя-владельца адреса
    """
    __tablename__ = 'addresses'

    id = Column(Integer, primary_key=True)
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=False)
    country = Column(String, nullable=False, default="Russia")
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Связи
    user = relationship("User", back_populates="addresses")
    orders = relationship("Order", back_populates="address")

    def __repr__(self):
        return f"<Address(id={self.id}, city='{self.city}', street='{self.street}')>"
