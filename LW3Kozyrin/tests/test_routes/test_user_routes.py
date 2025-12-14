"""
Тесты для API endpoints пользователей

Используется TestClient от Litestar для тестирования HTTP запросов
"""
import pytest
from litestar import Litestar
from litestar.testing import AsyncTestClient
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.controllers.user_controller import UserController
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.models.base import Base


@pytest.fixture(scope="function")
async def test_app():
    """
    Фикстура для создания тестового приложения Litestar

    Создает приложение с тестовой БД и всеми зависимостями
    """
    # Создаем тестовый движок БД
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Фабрика сессий
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Провайдеры зависимостей
    async def provide_db_session() -> AsyncSession:
        async with async_session_factory() as session:
            yield session
            await session.close()

    def provide_user_repository() -> UserRepository:
        return UserRepository()

    def provide_user_service(
        user_repository: UserRepository,
        db_session: AsyncSession
    ) -> UserService:
        return UserService(user_repository, db_session)

    # Создаем приложение
    app = Litestar(
        route_handlers=[UserController],
        dependencies={
            "db_session": Provide(provide_db_session),
            "user_repository": Provide(provide_user_repository, sync_to_thread=False),
            "user_service": Provide(provide_user_service, sync_to_thread=False),
        },
    )
    
    yield app
    
    # Очистка
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user_endpoint(test_app):
    """
    Тест создания пользователя через API
    
    Проверяет:
    - POST запрос на /users создает пользователя
    - Возвращается статус 201
    - Ответ содержит корректные данные пользователя
    """
    async with AsyncTestClient(app=test_app) as client:
        response = await client.post(
            "/users",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert "id" in data
        assert "created_at" in data


@pytest.mark.asyncio
async def test_get_user_by_id_endpoint(test_app):
    """
    Тест получения пользователя по ID через API
    
    Проверяет:
    - GET запрос на /users/{id} возвращает пользователя
    - Возвращается статус 200
    """
    async with AsyncTestClient(app=test_app) as client:
        # Создаем пользователя
        create_response = await client.post(
            "/users",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        )
        user_id = create_response.json()["id"]
        
        # Получаем пользователя
        get_response = await client.get(f"/users/{user_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == user_id
        assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_user_not_found(test_app):
    """
    Тест получения несуществующего пользователя
    
    Проверяет, что API возвращает 404 для несуществующего пользователя
    """
    async with AsyncTestClient(app=test_app) as client:
        response = await client.get("/users/9999")
        
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_all_users_endpoint(test_app):
    """
    Тест получения списка пользователей через API
    
    Проверяет:
    - GET запрос на /users возвращает список
    - Работает пагинация
    """
    async with AsyncTestClient(app=test_app) as client:
        # Создаем несколько пользователей
        for i in range(3):
            await client.post(
                "/users",
                json={
                    "username": f"user{i}",
                    "email": f"user{i}@example.com",
                    "full_name": f"User {i}"
                }
            )
        
        # Получаем список пользователей
        response = await client.get("/users?count=2&page=1")
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total_count" in data
        assert len(data["users"]) == 2
        assert data["total_count"] == 3


@pytest.mark.asyncio
async def test_update_user_endpoint(test_app):
    """
    Тест обновления пользователя через API
    
    Проверяет:
    - PUT запрос на /users/{id} обновляет данные
    - Возвращается статус 200
    """
    async with AsyncTestClient(app=test_app) as client:
        # Создаем пользователя
        create_response = await client.post(
            "/users",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        )
        user_id = create_response.json()["id"]
        
        # Обновляем пользователя
        update_response = await client.put(
            f"/users/{user_id}",
            json={
                "full_name": "Updated Name",
                "email": "updated@example.com"
            }
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["full_name"] == "Updated Name"
        assert data["email"] == "updated@example.com"
        assert data["username"] == "testuser"  # Не изменилось


@pytest.mark.asyncio
async def test_delete_user_endpoint(test_app):
    """
    Тест удаления пользователя через API
    
    Проверяет:
    - DELETE запрос на /users/{id} удаляет пользователя
    - Возвращается статус 200
    - После удаления пользователь не найден
    """
    async with AsyncTestClient(app=test_app) as client:
        # Создаем пользователя
        create_response = await client.post(
            "/users",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User"
            }
        )
        user_id = create_response.json()["id"]
        
        # Удаляем пользователя
        delete_response = await client.delete(f"/users/{user_id}")
        
        assert delete_response.status_code == 200
        assert "message" in delete_response.json()
        
        # Проверяем, что пользователь удален
        get_response = await client.get(f"/users/{user_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_user_validation_error(test_app):
    """
    Тест валидации данных при создании пользователя
    
    Проверяет, что API возвращает ошибку при невалидных данных
    """
    async with AsyncTestClient(app=test_app) as client:
        # Пытаемся создать пользователя с невалидным email
        response = await client.post(
            "/users",
            json={
                "username": "test",
                "email": "invalid-email",  # Невалидный email
                "full_name": "Test"
            }
        )
        
        assert response.status_code == 400  # Bad Request
