from litestar import Controller, get, post, put, delete
from litestar.di import Provide
from litestar.params import Parameter
from litestar.exceptions import NotFoundException
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse, UserListResponse
from typing import List


class UserController(Controller):
    """Контроллер для управления пользователями"""
    
    path = "/users"
    dependencies = {"user_service": Provide(lambda: None)}  # Будет переопределено в main.py

    @get("/{user_id:int}")
    async def get_user_by_id(
        self,
        user_service: UserService,
        user_id: int = Parameter(gt=0, description="ID пользователя"),
    ) -> UserResponse:
        """
        Получить пользователя по ID
        
        Args:
            user_service: Сервис для работы с пользователями
            user_id: ID пользователя
            
        Returns:
            UserResponse с данными пользователя
            
        Raises:
            NotFoundException: Если пользователь не найден
        """
        user = await user_service.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)

    @get()
    async def get_all_users(
        self,
        user_service: UserService,
        count: int = Parameter(10, gt=0, le=100, description="Количество записей на странице"),
        page: int = Parameter(1, gt=0, description="Номер страницы"),
    ) -> UserListResponse:
        """
        Получить список всех пользователей с пагинацией
        
        Args:
            user_service: Сервис для работы с пользователями
            count: Количество записей на странице (по умолчанию 10, максимум 100)
            page: Номер страницы (начиная с 1)
            
        Returns:
            UserListResponse со списком пользователей и общим количеством
        """
        users = await user_service.get_by_filter(count=count, page=page)
        total_count = await user_service.get_total_count()
        
        return UserListResponse(
            users=[UserResponse.model_validate(user) for user in users],
            total_count=total_count
        )

    @post()
    async def create_user(
        self,
        user_service: UserService,
        data: UserCreate,
    ) -> UserResponse:
        """
        Создать нового пользователя
        
        Args:
            user_service: Сервис для работы с пользователями
            data: Данные для создания пользователя
            
        Returns:
            UserResponse с данными созданного пользователя
        """
        user = await user_service.create(data)
        return UserResponse.model_validate(user)

    @delete("/{user_id:int}", status_code=200)
    async def delete_user(
            self,
            user_service: UserService,
            user_id: int = Parameter(gt=0, description="ID пользователя"),
    ) -> dict:
        """
        Удалить пользователя
        
        Args:
            user_service: Сервис для работы с пользователями
            user_id: ID пользователя
            
        Returns:
            Словарь с сообщением об успешном удалении
            
        Raises:
            NotFoundException: Если пользователь не найден
        """
        deleted = await user_service.delete(user_id)
        if not deleted:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return {"message": f"User with ID {user_id} successfully deleted"}

    @put("/{user_id:int}")
    async def update_user(
        self,
        user_service: UserService,
        user_id: int = Parameter(gt=0, description="ID пользователя"),
        data: UserUpdate = None,
    ) -> UserResponse:
        """
        Обновить данные пользователя
        
        Args:
            user_service: Сервис для работы с пользователями
            user_id: ID пользователя
            data: Новые данные пользователя
            
        Returns:
            UserResponse с данными обновленного пользователя
            
        Raises:
            NotFoundException: Если пользователь не найден
        """
        user = await user_service.update(user_id, data)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)
