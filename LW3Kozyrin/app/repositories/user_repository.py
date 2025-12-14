from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.cache.redis_client import redis_client
from typing import Optional
import json


class UserRepository:
    """Репозиторий для работы с пользователями в базе данных"""

    USER_CACHE_TTL = 3600

    async def get_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID с кэшированием

        Args:
            session: Сессия базы данных
            user_id: ID пользователя

        Returns:
            User или None, если пользователь не найден
        """
        cache_key = f"user:{user_id}"
        cached_data = await redis_client.get_json(cache_key)

        if cached_data:
            # Восстанавливаем объект User из кэша
            user = User(**cached_data)
            return user

        # Если данных нет в кэше, запрашиваем из БД
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user_dict = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name
            }
            await redis_client.set_json(cache_key, user_dict, expire=self.USER_CACHE_TTL)

        return user

    async def get_by_filter(
            self,
            session: AsyncSession,
            count: int = 10,
            page: int = 1,
            **kwargs
    ) -> list[User]:
        """
        Получить список пользователей с фильтрацией и пагинацией

        Args:
            session: Сессия базы данных
            count: Количество записей на странице
            page: Номер страницы (начиная с 1)
            **kwargs: Дополнительные фильтры (username, email и т.д.)

        Returns:
            Список пользователей
        """
        query = select(User)

        # Применяем фильтры, если они переданы
        if "username" in kwargs and kwargs["username"]:
            query = query.where(User.username == kwargs["username"])
        if "email" in kwargs and kwargs["email"]:
            query = query.where(User.email == kwargs["email"])

        # Вычисляем offset для пагинации
        offset = (page - 1) * count

        # Применяем пагинацию
        query = query.offset(offset).limit(count)

        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_total_count(self, session: AsyncSession) -> int:
        """
        Получить общее количество пользователей в базе данных

        Args:
            session: Сессия базы данных

        Returns:
            Общее количество пользователей
        """
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def create(self, session: AsyncSession, user_data: UserCreate) -> User:
        """
        Создать нового пользователя

        Args:
            session: Сессия базы данных
            user_data: Данные для создания пользователя

        Returns:
            Созданный пользователь
        """
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update(
            self,
            session: AsyncSession,
            user_id: int,
            user_data: UserUpdate
    ) -> Optional[User]:
        """
        Обновить данные пользователя

        Args:
            session: Сессия базы данных
            user_id: ID пользователя
            user_data: Новые данные пользователя

        Returns:
            Обновленный пользователь или None, если не найден
        """
        user = await self.get_by_id(session, user_id)
        if not user:
            return None

        # Обновляем только те поля, которые переданы
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await session.commit()
        await session.refresh(user)

        cache_key = f"user:{user_id}"
        await redis_client.delete(cache_key)

        return user

    async def delete(self, session: AsyncSession, user_id: int) -> bool:
        """
        Удалить пользователя

        Args:
            session: Сессия базы данных
            user_id: ID пользователя

        Returns:
            True, если пользователь был удален, False если не найден
        """
        user = await self.get_by_id(session, user_id)
        if not user:
            return False

        await session.delete(user)
        await session.commit()

        cache_key = f"user:{user_id}"
        await redis_client.delete(cache_key)

        return True
