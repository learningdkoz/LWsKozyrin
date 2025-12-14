"""
Тесты граничных случаев для заказов

Вопрос 3 из ЛР4: Граничные случаи для сервиса заказов
"""
import pytest
from app.schemas.order_schema import OrderCreate, OrderItemCreate
from app.schemas.user_schema import UserCreate
from app.schemas.address_schema import AddressCreate
from app.schemas.product_schema import ProductCreate


@pytest.mark.asyncio
async def test_order_with_zero_quantity(
    test_session,
    order_repository,
    user_repository,
    address_repository,
    product_repository
):
    """
    Edge case: Попытка создать заказ с нулевым количеством товара
    
    Проверяет, что система корректно обрабатывает невалидные данные
    """
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
    
    # Pydantic должна отклонить это на уровне валидации
    with pytest.raises(Exception):  # ValidationError
        OrderItemCreate(product_id=product.id, quantity=0)


@pytest.mark.asyncio
async def test_order_with_negative_quantity(
    test_session,
    order_repository,
    user_repository,
    address_repository,
    product_repository
):
    """
    Edge case: Попытка создать заказ с отрицательным количеством
    """
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
    
    with pytest.raises(Exception):  # ValidationError
        OrderItemCreate(product_id=product.id, quantity=-5)


@pytest.mark.asyncio
async def test_order_with_nonexistent_product(
    test_session,
    order_repository,
    user_repository,
    address_repository
):
    """
    Edge case: Попытка создать заказ с несуществующим продуктом
    
    Проверяет, что система выбрасывает ошибку при попытке
    добавить в заказ продукт, которого нет в БД
    """
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
    
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[OrderItemCreate(product_id=9999, quantity=1)]  # Несуществующий продукт
    )
    
    with pytest.raises(ValueError, match="Product with ID 9999 not found"):
        await order_repository.create(test_session, order_data)


@pytest.mark.asyncio
async def test_order_with_empty_items_list(
    test_session,
    order_repository,
    user_repository,
    address_repository
):
    """
    Edge case: Попытка создать заказ без товаров
    
    Заказ должен содержать хотя бы один товар
    """
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
    
    # Pydantic должна отклонить пустой список
    with pytest.raises(Exception):  # ValidationError
        OrderCreate(
            user_id=user.id,
            address_id=address.id,
            items=[]  # Пустой список
        )


@pytest.mark.asyncio
async def test_order_exceeding_stock_quantity(
    test_session,
    order_repository,
    user_repository,
    address_repository,
    product_repository
):
    """
    Edge case: Заказ товара в количестве, превышающем запасы на складе
    
    Это важный бизнес-кейс, который требует отдельной логики проверки
    """
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
    # Продукт с ограниченным количеством
    product = await product_repository.create(
        test_session,
        ProductCreate(name="Товар", price=1000.0, stock_quantity=5)
    )
    
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[OrderItemCreate(product_id=product.id, quantity=10)]  # Больше чем на складе
    )
    
    # В текущей реализации это создаст заказ, но в продакшене нужна проверка
    # Здесь мы демонстрируем, что нужно добавить валидацию
    order = await order_repository.create(test_session, order_data)
    assert order is not None
    # TODO: Добавить проверку stock_quantity в сервисном слое


@pytest.mark.asyncio
async def test_order_with_nonexistent_user(
    test_session,
    order_repository,
    address_repository,
    product_repository
):
    """
    Edge case: Попытка создать заказ для несуществующего пользователя
    """
    # Создаем фейковый адрес (это тоже приведет к ошибке, но для теста)
    # В реальной системе нужна проверка существования пользователя
    product = await product_repository.create(
        test_session,
        ProductCreate(name="Товар", price=1000.0, stock_quantity=10)
    )
    
    order_data = OrderCreate(
        user_id=9999,  # Несуществующий пользователь
        address_id=9999,  # Несуществующий адрес
        items=[OrderItemCreate(product_id=product.id, quantity=1)]
    )
    
    # SQLAlchemy должна выбросить IntegrityError из-за внешнего ключа
    with pytest.raises(Exception):  # IntegrityError
        await order_repository.create(test_session, order_data)


@pytest.mark.asyncio
async def test_order_with_very_large_quantity(
    test_session,
    order_repository,
    user_repository,
    address_repository,
    product_repository
):
    """
    Edge case: Заказ с очень большим количеством товара
    
    Проверяет корректность расчета общей стоимости при больших числах
    """
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
        ProductCreate(name="Товар", price=1000.0, stock_quantity=1000000)
    )
    
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[OrderItemCreate(product_id=product.id, quantity=10000)]
    )
    
    order = await order_repository.create(test_session, order_data)
    
    # Проверяем корректность расчета: 10000 * 1000 = 10,000,000
    assert order.total_price == 10000000.0


@pytest.mark.asyncio
async def test_order_with_multiple_same_products(
    test_session,
    order_repository,
    user_repository,
    address_repository,
    product_repository
):
    """
    Edge case: Заказ с одним и тем же продуктом несколько раз
    
    Проверяет, можно ли добавить один продукт несколько раз в заказ
    """
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
        ProductCreate(name="Товар", price=1000.0, stock_quantity=100)
    )
    
    # Добавляем один и тот же продукт дважды
    order_data = OrderCreate(
        user_id=user.id,
        address_id=address.id,
        items=[
            OrderItemCreate(product_id=product.id, quantity=2),
            OrderItemCreate(product_id=product.id, quantity=3)
        ]
    )
    
    order = await order_repository.create(test_session, order_data)
    
    # Должно быть 2 отдельных элемента заказа
    assert len(order.order_items) == 2
    # Общая стоимость: (2 + 3) * 1000 = 5000
    assert order.total_price == 5000.0
