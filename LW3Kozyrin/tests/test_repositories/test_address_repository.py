"""
Тесты для репозитория адресов

Проверяются операции CRUD для адресов
"""
import pytest
from app.schemas.address_schema import AddressCreate, AddressUpdate
from app.schemas.user_schema import UserCreate


@pytest.mark.asyncio
async def test_create_address(test_session, address_repository, user_repository):
    """Тест создания адреса"""
    # Сначала создаем пользователя
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User"
    )
    user = await user_repository.create(test_session, user_data)
    
    # Создаем адрес
    address_data = AddressCreate(
        street="ул. Ленина, 10",
        city="Москва",
        state="Московская область",
        zip_code="123456",
        country="Russia",
        user_id=user.id
    )
    
    address = await address_repository.create(test_session, address_data)
    
    assert address.id is not None
    assert address.street == "ул. Ленина, 10"
    assert address.city == "Москва"
    assert address.user_id == user.id


@pytest.mark.asyncio
async def test_get_address_by_id(test_session, address_repository, user_repository):
    """Тест получения адреса по ID"""
    user_data = UserCreate(username="testuser", email="test@example.com")
    user = await user_repository.create(test_session, user_data)
    
    address_data = AddressCreate(
        street="ул. Пушкина, 5",
        city="Санкт-Петербург",
        zip_code="654321",
        country="Russia",
        user_id=user.id
    )
    created_address = await address_repository.create(test_session, address_data)
    
    found_address = await address_repository.get_by_id(test_session, created_address.id)
    
    assert found_address is not None
    assert found_address.id == created_address.id
    assert found_address.city == "Санкт-Петербург"


@pytest.mark.asyncio
async def test_get_addresses_by_user_id(test_session, address_repository, user_repository):
    """Тест получения всех адресов пользователя"""
    user_data = UserCreate(username="testuser", email="test@example.com")
    user = await user_repository.create(test_session, user_data)
    
    # Создаем 2 адреса для пользователя
    for i in range(2):
        address_data = AddressCreate(
            street=f"ул. Тестовая, {i}",
            city="Москва",
            zip_code=f"12345{i}",
            country="Russia",
            user_id=user.id
        )
        await address_repository.create(test_session, address_data)
    
    addresses = await address_repository.get_by_user_id(test_session, user.id)
    assert len(addresses) == 2


@pytest.mark.asyncio
async def test_update_address(test_session, address_repository, user_repository):
    """Тест обновления адреса"""
    user_data = UserCreate(username="testuser", email="test@example.com")
    user = await user_repository.create(test_session, user_data)
    
    address_data = AddressCreate(
        street="ул. Старая, 1",
        city="Москва",
        zip_code="111111",
        country="Russia",
        user_id=user.id
    )
    address = await address_repository.create(test_session, address_data)
    
    update_data = AddressUpdate(
        street="ул. Новая, 2",
        zip_code="222222"
    )
    updated_address = await address_repository.update(test_session, address.id, update_data)
    
    assert updated_address is not None
    assert updated_address.street == "ул. Новая, 2"
    assert updated_address.zip_code == "222222"
    assert updated_address.city == "Москва"  # Не изменилось


@pytest.mark.asyncio
async def test_delete_address(test_session, address_repository, user_repository):
    """Тест удаления адреса"""
    user_data = UserCreate(username="testuser", email="test@example.com")
    user = await user_repository.create(test_session, user_data)
    
    address_data = AddressCreate(
        street="ул. Временная, 99",
        city="Казань",
        zip_code="999999",
        country="Russia",
        user_id=user.id
    )
    address = await address_repository.create(test_session, address_data)
    
    deleted = await address_repository.delete(test_session, address.id)
    assert deleted is True
    
    found_address = await address_repository.get_by_id(test_session, address.id)
    assert found_address is None
