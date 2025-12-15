from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional


class ReportBase(BaseModel):
    """Базовая схема отчета"""
    report_at: date
    order_id: int
    count_product: int


class ReportCreate(ReportBase):
    """Схема для создания отчета"""
    pass


class ReportResponse(ReportBase):
    """Схема ответа с отчетом"""
    id: int

    model_config = ConfigDict(from_attributes=True)


class ReportFilter(BaseModel):
    """Схема фильтра для получения отчетов"""
    report_date: date
