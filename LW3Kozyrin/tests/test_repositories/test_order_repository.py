"""
Тесты для репозитория заказов

Проверяются операции CRUD для заказов с поддержкой нескольких продуктов
"""
import pytest
from app.schemas.order_schema import OrderCreate, OrderUpdate, OrderItemCreate
from app.schemas.user_schema import UserCreate
from app.schemas.address_schema import AddressCreate
from app.schemas.product_schema import ProductCreate
from app.models.order import OrderStatus


@pytest.mark.asyncio
async def test_create_order_with_multiple_products(
    test_session, 
    order_repository, 
    user_repository,
    address_repository,
    product_repository
):
    """
    Тест создания заказа с несколькими продуктами
    
    Проверяет, что:
    - Заказ создается с несколькими товарами
    - Общая стоимость рассчитывается правильно
    - OrderItems создаются корректно
    """
    # Создаем пользователя
    user_data = UserCreate(username="testuser", email="test@example.com")
    user = await user_repository.create(test_session, user_data)
    
    # Создаем адрес
    address_data = AddressCreate(
        street="ул. Тестовая, 1",
        city="Москва",
        zip_code="123456",
        country="Russia",
        user_id=user.id
    )
    address = await address_repository.create(test_session, address_data)
    
    # Создаем продукты
    product1_data = ProductCreate(name="Товар 1", price=1000.0, stock_quantity=10)
    product2_data = ProductCreate(name="Товар 2", price=2000.0, stock_quantity=5)
    product1 = await product_repository.create(test_session, product1_data)
    product2 = await product_repository.create(test_session, product2_data)
    
    # Создаем заказ с 2 продуктами
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[
            OrderItemCreate(product_id=product1.id, quantity=2),  # 2 * 1000 = 2000
            OrderItemCreate(product_id=product2.id, quantity=1)   # 1 * 2000 = 2000
        ]
    )
    
    order = await order_repository.create(test_session, order_data)
    
    assert order.id is not None
    assert order.user_id == user.id
    assert order.total_price == 4000.0, "Общая стоимость должна быть 4000"
    assert len(order.order_items) == 2, "Должно быть 2 элемента заказа"
    assert order.status == OrderStatus.PENDING


@pytest.mark.asyncio
async def test_get_order_by_id(
    test_session, 
    order_repository, 
    user_repository,
    address_repository,
    product_repository
):
    """Тест получения заказа по ID"""
    # Подготовка данных
    user = await user_repository.create(
        test_session, 
        UserCreate(username="testuser", email="test@example.com")
    )
    address = await address_repository.create(
        test_session,
        AddressCreate(
            street="ул. Тестовая, 1",
            city="Москва",
            zip_code="123456",
            country="Russia",
            user_id=user.id
        )
    )
    product = await product_repository.create(
        test_session,
        ProductCreate(name="Товар", price=1000.0, stock_quantity=10)
    )
    
    # Создаем заказ
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[OrderItemCreate(product_id=product.id, quantity=1)]
    )
    created_order = await order_repository.create(test_session, order_data)
    
    # Получаем заказ
    found_order = await order_repository.get_by_id(test_session, created_order.id)
    
    assert found_order is not None
    assert found_order.id == created_order.id
    assert len(found_order.order_items) == 1


@pytest.mark.asyncio
async def test_get_orders_by_user_id(
    test_session, 
    order_repository, 
    user_repository,
    address_repository,
    product_repository
):
    """Тест получения всех заказов пользователя"""
    user = await user_repository.create(
        test_session, 
        UserCreate(username="testuser", email="test@example.com")
    )
    address = await address_repository.create(
        test_session,
        AddressCreate(
            street="ул. Тестовая, 1",
            city="Москва",
            zip_code="123456",
            country="Russia",
            user_id=user.id
        )
    )
    product = await product_repository.create(
        test_session,
        ProductCreate(name="Товар", price=1000.0, stock_quantity=10)
    )
    
    # Создаем 2 заказа
    for i in range(2):
        order_data = OrderCreate(
            user_id=user.id,
            address_id=address.id,
            items=[OrderItemCreate(product_id=product.id, quantity=1)]
        )
        await order_repository.create(test_session, order_data)
    
    orders = await order_repository.get_by_user_id(test_session, user.id)
    assert len(orders) == 2


@pytest.mark.asyncio
async def test_update_order_status(
    test_session, 
    order_repository, 
    user_repository,
    address_repository,
    product_repository
):
    """Тест обновления статуса заказа"""
    # Подготовка
    user = await user_repository.create(
        test_session, 
        UserCreate(username="testuser", email="test@example.com")
    )
    address = await address_repository.create(
        test_session,
        AddressCreate(
            street="ул. Тестовая, 1",
            city="Москва",
            zip_code="123456",
            country="Russia",
            user_id=user.id
        )
    )
    product = await product_repository.create(
        test_session,
        ProductCreate(name="Товар", price=1000.0, stock_quantity=10)
    )
    
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[OrderItemCreate(product_id=product.id, quantity=1)]
    )
    order = await order_repository.create(test_session, order_data)
    
    # Обновляем статус
    update_data = OrderUpdate(status=OrderStatus.SHIPPED)
    updated_order = await order_repository.update(test_session, order.id, update_data)
    
    assert updated_order is not None
    assert updated_order.status == OrderStatus.SHIPPED


@pytest.mark.asyncio
async def test_delete_order(
    test_session, 
    order_repository, 
    user_repository,
    address_repository,
    product_repository
):
    """Тест удаления заказа"""
    user = await user_repository.create(
        test_session, 
        UserCreate(username="testuser", email="test@example.com")
    )
    address = await address_repository.create(
        test_session,
        AddressCreate(
            street="ул. Тестовая, 1",
            city="Москва",
            zip_code="123456",
            country="Russia",
            user_id=user.id
        )
    )
    product = await product_repository.create(
        test_session,
        ProductCreate(name="Товар", price=1000.0, stock_quantity=10)
    )
    
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[OrderItemCreate(product_id=product.id, quantity=1)]
    )
    order = await order_repository.create(test_session, order_data)
    
    deleted = await order_repository.delete(test_session, order.id)
    assert deleted is True
    
    found_order = await order_repository.get_by_id(test_session, order.id)
    assert found_order is None


@pytest.mark.asyncio
async def test_get_orders_with_pagination(
    test_session, 
    order_repository, 
    user_repository,
    address_repository,
    product_repository
):
    """Тест пагинации заказов"""
    user = await user_repository.create(
        test_session, 
        UserCreate(username="testuser", email="test@example.com")
    )
    address = await address_repository.create(
        test_session,
        AddressCreate(
            street="ул. Тестовая, 1",
            city="Москва",
            zip_code="123456",
            country="Russia",
            user_id=user.id
        )
    )
    product = await product_repository.create(
        test_session,
        ProductCreate(name="Товар", price=1000.0, stock_quantity=10)
    )
    
    # Создаем 5 заказов
    for i in range(5):
        order_data = OrderCreate(
            user_id=user.id,
            address_id=address.id,
            items=[OrderItemCreate(product_id=product.id, quantity=1)]
        )
        await order_repository.create(test_session, order_data)
    
    # Проверяем пагинацию
    page1 = await order_repository.get_by_filter(test_session, count=2, page=1)
    assert len(page1) == 2
    
    total_count = await order_repository.get_total_count(test_session)
    assert total_count == 5
