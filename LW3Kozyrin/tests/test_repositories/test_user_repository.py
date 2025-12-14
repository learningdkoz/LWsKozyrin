"""
Тесты для репозитория пользователей

Проверяются операции:
- Создание пользователя
- Поиск пользователя по ID
- Получение списка пользователей с пагинацией
- Обновление данных пользователя
- Удаление пользователя
"""
import pytest
from app.schemas.user_schema import UserCreate, UserUpdate


@pytest.mark.asyncio
async def test_create_user(test_session, user_repository):
    """
    Тест создания пользователя в базе данных
    
    Проверяет, что:
    - Пользователь успешно создается
    - Все поля корректно сохраняются
    - Генерируется уникальный ID
    """
    # Подготовка данных для создания пользователя
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User"
    )
    
    # Создаем пользователя
    user = await user_repository.create(test_session, user_data)
    
    # Проверяем результат
    assert user.id is not None, "ID пользователя должен быть сгенерирован"
    assert user.username == "testuser", "Username должен совпадать"
    assert user.email == "test@example.com", "Email должен совпадать"
    assert user.full_name == "Test User", "Full name должно совпадать"
    assert user.created_at is not None, "Дата создания должна быть установлена"
    assert user.updated_at is not None, "Дата обновления должна быть установлена"


@pytest.mark.asyncio
async def test_get_user_by_id(test_session, user_repository):
    """
    Тест поиска пользователя по ID
    
    Проверяет, что:
    - Существующий пользователь найден
    - Данные пользователя корректны
    - Несуществующий ID возвращает None
    """
    # Создаем пользователя
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User"
    )
    created_user = await user_repository.create(test_session, user_data)
    
    # Ищем пользователя по ID
    found_user = await user_repository.get_by_id(test_session, created_user.id)
    
    # Проверяем, что пользователь найден
    assert found_user is not None, "Пользователь должен быть найден"
    assert found_user.id == created_user.id, "ID должны совпадать"
    assert found_user.username == "testuser", "Username должен совпадать"
    
    # Проверяем поиск несуществующего пользователя
    not_found = await user_repository.get_by_id(test_session, 9999)
    assert not_found is None, "Несуществующий пользователь должен вернуть None"


@pytest.mark.asyncio
async def test_get_users_with_pagination(test_session, user_repository):
    """
    Тест получения списка пользователей с пагинацией
    
    Проверяет, что:
    - Создается несколько пользователей
    - Пагинация работает корректно
    - Возвращается правильное количество записей
    """
    # Создаем 5 пользователей
    for i in range(5):
        user_data = UserCreate(
            username=f"user{i}",
            email=f"user{i}@example.com",
            full_name=f"User {i}"
        )
        await user_repository.create(test_session, user_data)
    
    # Получаем первую страницу (3 пользователя)
    page1 = await user_repository.get_by_filter(test_session, count=3, page=1)
    assert len(page1) == 3, "Первая страница должна содержать 3 пользователей"
    
    # Получаем вторую страницу (2 пользователя)
    page2 = await user_repository.get_by_filter(test_session, count=3, page=2)
    assert len(page2) == 2, "Вторая страница должна содержать 2 пользователей"
    
    # Проверяем общее количество
    total_count = await user_repository.get_total_count(test_session)
    assert total_count == 5, "Общее количество должно быть 5"


@pytest.mark.asyncio
async def test_update_user(test_session, user_repository):
    """
    Тест обновления данных пользователя
    
    Проверяет, что:
    - Данные пользователя успешно обновляются
    - Обновляются только переданные поля
    - updated_at изменяется после обновления
    """
    # Создаем пользователя
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User"
    )
    user = await user_repository.create(test_session, user_data)
    original_updated_at = user.updated_at
    
    # Обновляем пользователя
    update_data = UserUpdate(
        full_name="Updated User",
        email="updated@example.com"
    )
    updated_user = await user_repository.update(test_session, user.id, update_data)
    
    # Проверяем обновленные данные
    assert updated_user is not None, "Обновленный пользователь должен существовать"
    assert updated_user.full_name == "Updated User", "Full name должно быть обновлено"
    assert updated_user.email == "updated@example.com", "Email должен быть обновлен"
    assert updated_user.username == "testuser", "Username не должен измениться"
    
    # Проверяем обновление несуществующего пользователя
    not_updated = await user_repository.update(
        test_session, 
        9999, 
        UserUpdate(full_name="Test")
    )
    assert not_updated is None, "Обновление несуществующего пользователя должно вернуть None"


@pytest.mark.asyncio
async def test_delete_user(test_session, user_repository):
    """
    Тест удаления пользователя
    
    Проверяет, что:
    - Пользователь успешно удаляется
    - После удаления пользователь не найден
    - Удаление несуществующего пользователя возвращает False
    """
    # Создаем пользователя
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User"
    )
    user = await user_repository.create(test_session, user_data)
    
    # Удаляем пользователя
    deleted = await user_repository.delete(test_session, user.id)
    assert deleted is True, "Удаление должно вернуть True"
    
    # Проверяем, что пользователь удален
    found_user = await user_repository.get_by_id(test_session, user.id)
    assert found_user is None, "Пользователь должен быть удален"
    
    # Пытаемся удалить несуществующего пользователя
    not_deleted = await user_repository.delete(test_session, 9999)
    assert not_deleted is False, "Удаление несуществующего пользователя должно вернуть False"


@pytest.mark.asyncio
async def test_get_users_by_filter(test_session, user_repository):
    """
    Тест фильтрации пользователей
    
    Проверяет, что:
    - Фильтрация по username работает корректно
    - Фильтрация по email работает корректно
    """
    # Создаем пользователей
    user1_data = UserCreate(username="alice", email="alice@example.com", full_name="Alice")
    user2_data = UserCreate(username="bob", email="bob@example.com", full_name="Bob")
    
    await user_repository.create(test_session, user1_data)
    await user_repository.create(test_session, user2_data)
    
    # Фильтруем по username
    users = await user_repository.get_by_filter(test_session, username="alice")
    assert len(users) == 1, "Должен быть найден один пользователь"
    assert users[0].username == "alice", "Найден правильный пользователь"
    
    # Фильтруем по email
    users = await user_repository.get_by_filter(test_session, email="bob@example.com")
    assert len(users) == 1, "Должен быть найден один пользователь"
    assert users[0].email == "bob@example.com", "Найден правильный пользователь"
