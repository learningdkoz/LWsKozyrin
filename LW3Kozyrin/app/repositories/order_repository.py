from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.models.address import Address
from app.schemas.order_schema import OrderCreate, OrderUpdate
from typing import Optional, List


class OrderRepository:
    """Репозиторий для работы с заказами в базе данных"""

    async def get_by_id(self, session: AsyncSession, order_id: int) -> Optional[Order]:
        """
        Получить заказ по ID вместе со всеми связанными данными

        Args:
            session: Сессия базы данных
            order_id: ID заказа

        Returns:
            Order или None
        """
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.order_items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, session: AsyncSession, user_id: int) -> List[Order]:
        """Получить все заказы пользователя"""
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.order_items))
            .where(Order.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_filter(
            self,
            session: AsyncSession,
            count: int = 10,
            page: int = 1,
            **kwargs
    ) -> List[Order]:
        """Получить список заказов с фильтрацией и пагинацией"""
        query = select(Order).options(selectinload(Order.order_items))

        if "user_id" in kwargs and kwargs["user_id"]:
            query = query.where(Order.user_id == kwargs["user_id"])
        if "status" in kwargs and kwargs["status"]:
            query = query.where(Order.status == kwargs["status"])

        offset = (page - 1) * count
        query = query.offset(offset).limit(count)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_total_count(self, session: AsyncSession) -> int:
        """Получить общее количество заказов"""
        result = await session.execute(select(func.count(Order.id)))
        return result.scalar_one()

    async def create(self, session: AsyncSession, order_data: OrderCreate) -> Order:
        """
        Создать новый заказ с несколькими продуктами

        Args:
            session: Сессия базы данных
            order_data: Данные для создания заказа (включая список товаров)

        Returns:
            Созданный заказ

        Raises:
            ValueError: Если пользователь, адрес или продукт не найдены
        """
        user_result = await session.execute(
            select(User).where(User.id == order_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User with ID {order_data.user_id} not found")

        address_result = await session.execute(
            select(Address).where(Address.id == order_data.address_id)
        )
        address = address_result.scalar_one_or_none()
        if not address:
            raise ValueError(f"Address with ID {order_data.address_id} not found")

        # Создаем заказ
        order = Order(
            user_id=order_data.user_id,
            address_id=order_data.address_id,
            total_price=0.0
        )
        session.add(order)
        await session.flush()  # Получаем ID заказа

        # Добавляем товары в заказ и подсчитываем общую стоимость
        total_price = 0.0
        for item_data in order_data.items:
            # Получаем продукт для получения его цены
            product_result = await session.execute(
                select(Product).where(Product.id == item_data.product_id)
            )
            product = product_result.scalar_one_or_none()
            if not product:
                raise ValueError(f"Product with ID {item_data.product_id} not found")

            # Создаем элемент заказа
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                price_at_purchase=product.price
            )
            session.add(order_item)
            total_price += product.price * item_data.quantity

        # Обновляем общую стоимость заказа
        order.total_price = total_price

        await session.commit()
        await session.refresh(order)

        # Загружаем order_items
        result = await session.execute(
            select(Order)
            .options(selectinload(Order.order_items))
            .where(Order.id == order.id)
        )
        return result.scalar_one()

    async def update(
            self,
            session: AsyncSession,
            order_id: int,
            order_data: OrderUpdate
    ) -> Optional[Order]:
        """Обновить данные заказа"""
        order = await self.get_by_id(session, order_id)
        if not order:
            return None

        update_data = order_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)

        await session.commit()
        await session.refresh(order)
        return order

    async def delete(self, session: AsyncSession, order_id: int) -> bool:
        """Удалить заказ"""
        order = await self.get_by_id(session, order_id)
        if not order:
            return False

        await session.delete(order)
        await session.commit()
        return True
