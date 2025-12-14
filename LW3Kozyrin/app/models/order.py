from sqlalchemy import Column, Integer, DateTime, ForeignKey, Float, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import Base


class OrderStatus(str, enum.Enum):
    """Статусы заказа"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(Base):
    """
    Модель заказа

    Attributes:
        id: Уникальный идентификатор заказа
        user_id: ID пользователя, сделавшего заказ
        address_id: ID адреса доставки
        status: Статус заказа
        total_price: Общая стоимость заказа
        created_at: Дата создания заказа
        updated_at: Дата последнего обновления заказа
    """
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_price = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи
    user = relationship("User", back_populates="orders")
    address = relationship("Address", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status='{self.status}', total={self.total_price})>"


class OrderItem(Base):
    """
    Промежуточная модель для связи заказа и продукта (many-to-many)
    Позволяет добавлять несколько продуктов в один заказ с указанием количества

    Attributes:
        id: Уникальный идентификатор записи
        order_id: ID заказа
        product_id: ID продукта
        quantity: Количество единиц продукта в заказе
        price_at_purchase: Цена продукта на момент покупки
    """
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price_at_purchase = Column(Float, nullable=False)

    # Связи
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(order_id={self.order_id}, product_id={self.product_id}, quantity={self.quantity})>"
