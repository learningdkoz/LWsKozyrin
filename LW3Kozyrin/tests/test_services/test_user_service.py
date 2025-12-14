"""
Тесты для сервиса пользователей с использованием mock

Mock позволяет тестировать сервисный слой независимо от репозитория и БД
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserUpdate
from app.models.user import User
from datetime import datetime


@pytest.fixture
def mock_user_repository():
    """Фикстура для создания mock репозитория"""
    return AsyncMock()


@pytest.fixture
def mock_session():
    """Фикстура для создания mock сессии БД"""
    return MagicMock()


@pytest.fixture
def user_service(mock_user_repository, mock_session):
    """Фикстура для создания сервиса с mock зависимостями"""
    return UserService(mock_user_repository, mock_session)


@pytest.mark.asyncio
async def test_create_user_service(user_service, mock_user_repository, mock_session):
    """
    Тест создания пользователя через сервис
    
    Проверяет, что:
    - Сервис вызывает метод репозитория create
    - Передаются правильные параметры
    - Возвращается созданный пользователь
    """
    # Подготавливаем тестовые данные
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User"
    )
    
    # Создаем mock объект пользователя
    mock_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Настраиваем mock репозитория для возврата mock пользователя
    mock_user_repository.create.return_value = mock_user
    
    # Вызываем метод сервиса
    result = await user_service.create(user_data)
    
    # Проверяем, что метод репозитория был вызван с правильными параметрами
    mock_user_repository.create.assert_called_once_with(mock_session, user_data)
    
    # Проверяем результат
    assert result.id == 1
    assert result.username == "testuser"
    assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_service(user_service, mock_user_repository, mock_session):
    """
    Тест получения пользователя по ID через сервис
    
    Проверяет, что сервис корректно вызывает репозиторий
    """
    # Mock пользователь
    mock_user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Настраиваем mock репозитория
    mock_user_repository.get_by_id.return_value = mock_user
    
    # Вызываем метод сервиса
    result = await user_service.get_by_id(1)
    
    # Проверяем вызов репозитория
    mock_user_repository.get_by_id.assert_called_once_with(mock_session, 1)
    
    # Проверяем результат
    assert result is not None
    assert result.id == 1
    assert result.username == "testuser"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_service, mock_user_repository, mock_session):
    """
    Тест получения несуществующего пользователя
    
    Проверяет, что сервис возвращает None для несуществующего пользователя
    """
    # Настраиваем mock для возврата None
    mock_user_repository.get_by_id.return_value = None
    
    # Вызываем метод сервиса
    result = await user_service.get_by_id(999)
    
    # Проверяем результат
    assert result is None
    mock_user_repository.get_by_id.assert_called_once_with(mock_session, 999)


@pytest.mark.asyncio
async def test_update_user_service(user_service, mock_user_repository, mock_session):
    """
    Тест обновления пользователя через сервис
    
    Проверяет правильность передачи данных в репозиторий
    """
    update_data = UserUpdate(
        full_name="Updated Name",
        email="updated@example.com"
    )
    
    mock_updated_user = User(
        id=1,
        username="testuser",
        email="updated@example.com",
        full_name="Updated Name",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    mock_user_repository.update.return_value = mock_updated_user
    
    result = await user_service.update(1, update_data)
    
    mock_user_repository.update.assert_called_once_with(mock_session, 1, update_data)
    assert result.email == "updated@example.com"
    assert result.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_delete_user_service(user_service, mock_user_repository, mock_session):
    """
    Тест удаления пользователя через сервис
    """
    mock_user_repository.delete.return_value = True
    
    result = await user_service.delete(1)
    
    mock_user_repository.delete.assert_called_once_with(mock_session, 1)
    assert result is True


@pytest.mark.asyncio
async def test_get_by_filter_service(user_service, mock_user_repository, mock_session):
    """
    Тест получения списка пользователей с фильтрацией
    """
    mock_users = [
        User(id=1, username="user1", email="user1@example.com", created_at=datetime.now(), updated_at=datetime.now()),
        User(id=2, username="user2", email="user2@example.com", created_at=datetime.now(), updated_at=datetime.now())
    ]
    
    mock_user_repository.get_by_filter.return_value = mock_users
    
    result = await user_service.get_by_filter(count=10, page=1, username="user")
    
    mock_user_repository.get_by_filter.assert_called_once_with(
        mock_session, 10, 1, username="user"
    )
    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_total_count_service(user_service, mock_user_repository, mock_session):
    """
    Тест получения общего количества пользователей
    """
    mock_user_repository.get_total_count.return_value = 42
    
    result = await user_service.get_total_count()
    
    mock_user_repository.get_total_count.assert_called_once_with(mock_session)
    assert result == 42
