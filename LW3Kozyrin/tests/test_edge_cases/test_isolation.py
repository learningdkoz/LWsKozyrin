"""
Тесты изоляции тестов

Вопрос 6 из ЛР4: Как обеспечить изоляцию тестов друг от друга
"""
import pytest
from app.schemas.user_schema import UserCreate


@pytest.mark.asyncio
async def test_isolation_test_1(test_session, user_repository):
    """
    Первый тест для проверки изоляции
    
    Создает пользователя и проверяет, что он единственный в БД
    """
    user_data = UserCreate(
        username="isolation_user_1",
        email="isolation1@example.com"
    )
    user = await user_repository.create(test_session, user_data)
    
    # Проверяем, что в БД только один пользователь
    total_count = await user_repository.get_total_count(test_session)
    assert total_count == 1, "В изолированном тесте должен быть только один пользователь"
    
    assert user.username == "isolation_user_1"


@pytest.mark.asyncio
async def test_isolation_test_2(test_session, user_repository):
    """
    Второй тест для проверки изоляции
    
    Создает другого пользователя и проверяет, что данные из первого теста не сохранились
    
    Изоляция обеспечивается:
    1. Использованием scope="function" для фикстуры test_session
    2. Использованием in-memory SQLite БД
    3. Пересозданием БД для каждого теста
    4. Откатом транзакций после каждого теста
    """
    user_data = UserCreate(
        username="isolation_user_2",
        email="isolation2@example.com"
    )
    user = await user_repository.create(test_session, user_data)
    
    # Проверяем, что в БД снова только один пользователь
    # Это доказывает, что данные из предыдущего теста не сохранились
    total_count = await user_repository.get_total_count(test_session)
    assert total_count == 1, "Тесты должны быть изолированы друг от друга"
    
    # Проверяем, что это новый пользователь, а не из первого теста
    assert user.username == "isolation_user_2"
    
    # Проверяем, что пользователь из первого теста не существует
    users = await user_repository.get_by_filter(test_session, username="isolation_user_1")
    assert len(users) == 0, "Данные из других тестов не должны быть доступны"


@pytest.mark.asyncio
async def test_isolation_concurrent_test(test_session, user_repository):
    """
    Тест параллельного выполнения
    
    Даже при параллельном выполнении (pytest -n auto) каждый тест
    должен иметь свою изолированную среду
    """
    user_data = UserCreate(
        username="concurrent_user",
        email="concurrent@example.com"
    )
    await user_repository.create(test_session, user_data)
    
    total_count = await user_repository.get_total_count(test_session)
    assert total_count == 1, "Параллельные тесты также должны быть изолированы"
