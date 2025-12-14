from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional


class UserService:
    """Сервисный слой для работы с пользователями"""
    
    def __init__(self, user_repository: UserRepository, db_session: AsyncSession):
        self.user_repository = user_repository
        self.db_session = db_session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Получить пользователя по ID
        
        Args:
            user_id: ID пользователя
            
        Returns:
            User или None
        """
        return await self.user_repository.get_by_id(self.db_session, user_id)

    async def get_by_filter(
        self, 
        count: int = 10, 
        page: int = 1, 
        **kwargs
    ) -> list[User]:
        """
        Получить список пользователей с фильтрацией
        
        Args:
            count: Количество записей на странице
            page: Номер страницы
            **kwargs: Дополнительные фильтры
            
        Returns:
            Список пользователей
        """
        return await self.user_repository.get_by_filter(
            self.db_session, count, page, **kwargs
        )

    async def get_total_count(self) -> int:
        """
        Получить общее количество пользователей
        
        Returns:
            Общее количество пользователей
        """
        return await self.user_repository.get_total_count(self.db_session)

    async def create(self, user_data: UserCreate) -> User:
        """
        Создать нового пользователя
        
        Args:
            user_data: Данные для создания пользователя
            
        Returns:
            Созданный пользователь
        """
        # Здесь может быть бизнес-логика, например:
        # - Проверка уникальности email
        # - Хеширование пароля
        # - Отправка приветственного письма
        return await self.user_repository.create(self.db_session, user_data)

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Обновить данные пользователя
        
        Args:
            user_id: ID пользователя
            user_data: Новые данные пользователя
            
        Returns:
            Обновленный пользователь или None
        """
        return await self.user_repository.update(self.db_session, user_id, user_data)

    async def delete(self, user_id: int) -> bool:
        """
        Удалить пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            True если удален, False если не найден
        """
        return await self.user_repository.delete(self.db_session, user_id)
