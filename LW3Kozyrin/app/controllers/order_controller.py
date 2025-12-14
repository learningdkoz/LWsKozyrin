"""Контроллер для работы с заказами через REST API"""
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.order_repository import OrderRepository
from app.schemas.order_schema import OrderResponse, OrderListResponse
from typing import Optional


class OrderController(Controller):
    """Контроллер для HTTP endpoints заказов"""
    path = "/orders"

    @get("/{order_id:int}")
    async def get_order(
            self,
            order_id: int,
            db_session: AsyncSession,
            order_repository: OrderRepository
    ) -> OrderResponse:
        """
        Получить заказ по ID

        Args:
            order_id: ID заказа
        """
        order = await order_repository.get_by_id(db_session, order_id)
        if not order:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Заказ с ID {order_id} не найден")
        return OrderResponse.model_validate(order)

    @get("/")
    async def get_all_orders(
            self,
            db_session: AsyncSession,
            order_repository: OrderRepository,
            count: int = 10,
            page: int = 1,
            user_id: Optional[int] = None,
            status: Optional[str] = None,
    ) -> OrderListResponse:
        """
        Получить список заказов с фильтрацией и пагинацией

        Args:
            count: Количество записей на странице
            page: Номер страницы
            user_id: Фильтр по ID пользователя
            status: Фильтр по статусу
        """
        orders = await order_repository.get_by_filter(
            db_session,
            count=count,
            page=page,
            user_id=user_id,
            status=status
        )
        total_count = await order_repository.get_total_count(db_session)

        return OrderListResponse(
            orders=[OrderResponse.model_validate(o) for o in orders],
            total_count=total_count
        )

    @get("/user/{user_id:int}")
    async def get_user_orders(
            self,
            user_id: int,
            db_session: AsyncSession,
            order_repository: OrderRepository
    ) -> OrderListResponse:
        """
        Получить все заказы конкретного пользователя

        Args:
            user_id: ID пользователя
        """
        orders = await order_repository.get_by_user_id(db_session, user_id)

        return OrderListResponse(
            orders=[OrderResponse.model_validate(o) for o in orders],
            total_count=len(orders)
        )
