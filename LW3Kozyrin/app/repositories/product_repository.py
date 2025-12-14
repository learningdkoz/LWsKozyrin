from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.product import Product
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.cache.redis_client import redis_client
from typing import Optional, List


class ProductRepository:
    """Репозиторий для работы с продуктами в базе данных"""

    PRODUCT_CACHE_TTL = 600

    async def get_by_id(self, session: AsyncSession, product_id: int) -> Optional[Product]:
        """
        Получить продукт по ID с кэшированием

        Args:
            session: Сессия базы данных
            product_id: ID продукта

        Returns:
            Product или None, если продукт не найден
        """
        cache_key = f"product:{product_id}"
        cached_data = await redis_client.get_json(cache_key)

        if cached_data:
            # Восстанавливаем объект Product из кэша
            product = Product(**cached_data)
            return product

        # Если данных нет в кэше, запрашиваем из БД
        result = await session.execute(
            select(Product).where(Product.id == product_id)
        )
        product = result.scalar_one_or_none()

        if product:
            product_dict = {
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "stock_quantity": product.stock_quantity
            }
            await redis_client.set_json(cache_key, product_dict, expire=self.PRODUCT_CACHE_TTL)

        return product

    async def get_by_filter(
            self,
            session: AsyncSession,
            count: int = 10,
            page: int = 1,
            **kwargs
    ) -> List[Product]:
        """
        Получить список продуктов с фильтрацией и пагинацией

        Args:
            session: Сессия базы данных
            count: Количество записей на странице
            page: Номер страницы
            **kwargs: Дополнительные фильтры

        Returns:
            Список продуктов
        """
        query = select(Product)

        # Применяем фильтры
        if "name" in kwargs and kwargs["name"]:
            query = query.where(Product.name.ilike(f"%{kwargs['name']}%"))
        if "min_price" in kwargs and kwargs["min_price"]:
            query = query.where(Product.price >= kwargs["min_price"])
        if "max_price" in kwargs and kwargs["max_price"]:
            query = query.where(Product.price <= kwargs["max_price"])

        # Пагинация
        offset = (page - 1) * count
        query = query.offset(offset).limit(count)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_total_count(self, session: AsyncSession) -> int:
        """Получить общее количество продуктов"""
        result = await session.execute(select(func.count(Product.id)))
        return result.scalar_one()

    async def create(self, session: AsyncSession, product_data: ProductCreate) -> Product:
        """
        Создать новый продукт

        Args:
            session: Сессия базы данных
            product_data: Данные для создания продукта

        Returns:
            Созданный продукт
        """
        product = Product(
            name=product_data.name,
            price=product_data.price,
            stock_quantity=product_data.stock_quantity
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    async def update(
            self,
            session: AsyncSession,
            product_id: int,
            product_data: ProductUpdate
    ) -> Optional[Product]:
        """
        Обновить данные продукта

        Args:
            session: Сессия базы данных
            product_id: ID продукта
            product_data: Новые данные продукта

        Returns:
            Обновленный продукт или None
        """
        product = await self.get_by_id(session, product_id)
        if not product:
            return None

        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await session.commit()
        await session.refresh(product)

        cache_key = f"product:{product_id}"
        product_dict = {
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "stock_quantity": product.stock_quantity
        }
        await redis_client.set_json(cache_key, product_dict, expire=self.PRODUCT_CACHE_TTL)

        return product

    async def delete(self, session: AsyncSession, product_id: int) -> bool:
        """
        Удалить продукт

        Args:
            session: Сессия базы данных
            product_id: ID продукта

        Returns:
            True если удален, False если не найден
        """
        product = await self.get_by_id(session, product_id)
        if not product:
            return False

        await session.delete(product)
        await session.commit()

        cache_key = f"product:{product_id}"
        await redis_client.delete(cache_key)

        return True
