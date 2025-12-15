from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date
from app.models.base import Base


class Report(Base):
    """
    Модель отчета по заказам

    Attributes:
        id: Уникальный идентификатор отчета
        report_at: Дата отчета
        order_id: ID заказа
        count_product: Количество продуктов в заказе
    """
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    report_at = Column(Date, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    count_product = Column(Integer, nullable=False)

    # Связи
    order = relationship("Order")

    def __repr__(self):
        return f"<Report(id={self.id}, report_at={self.report_at}, order_id={self.order_id}, count={self.count_product})>"
