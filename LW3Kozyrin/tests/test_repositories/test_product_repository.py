"""
Тесты для репозитория продуктов

Проверяются операции CRUD для продуктов
"""
import pytest
from app.schemas.product_schema import ProductCreate, ProductUpdate


@pytest.mark.asyncio
async def test_create_product(test_session, product_repository):
    """Тест создания продукта"""
    product_data = ProductCreate(
        name="Ноутбук",
        price=50000.0,
        stock_quantity=10
    )
    
    product = await product_repository.create(test_session, product_data)
    
    assert product.id is not None
    assert product.name == "Ноутбук"
    assert product.price == 50000.0
    assert product.stock_quantity == 10


@pytest.mark.asyncio
async def test_get_product_by_id(test_session, product_repository):
    """Тест получения продукта по ID"""
    product_data = ProductCreate(
        name="Мышь",
        price=1000.0,
        stock_quantity=50
    )
    created_product = await product_repository.create(test_session, product_data)
    
    found_product = await product_repository.get_by_id(test_session, created_product.id)
    
    assert found_product is not None
    assert found_product.id == created_product.id
    assert found_product.name == "Мышь"


@pytest.mark.asyncio
async def test_get_products_list(test_session, product_repository):
    """Тест получения списка продуктов с пагинацией"""
    # Создаем 3 продукта
    for i in range(3):
        product_data = ProductCreate(
            name=f"Товар {i}",
            price=1000.0 * (i + 1),
            stock_quantity=10 * (i + 1)
        )
        await product_repository.create(test_session, product_data)
    
    products = await product_repository.get_by_filter(test_session, count=2, page=1)
    assert len(products) == 2
    
    total_count = await product_repository.get_total_count(test_session)
    assert total_count == 3


@pytest.mark.asyncio
async def test_update_product(test_session, product_repository):
    """Тест обновления продукта"""
    product_data = ProductCreate(
        name="Клавиатура",
        price=3000.0,
        stock_quantity=20
    )
    product = await product_repository.create(test_session, product_data)
    
    update_data = ProductUpdate(
        price=3500.0,
        stock_quantity=15
    )
    updated_product = await product_repository.update(test_session, product.id, update_data)
    
    assert updated_product is not None
    assert updated_product.price == 3500.0
    assert updated_product.stock_quantity == 15
    assert updated_product.name == "Клавиатура"  # Не изменилось


@pytest.mark.asyncio
async def test_delete_product(test_session, product_repository):
    """Тест удаления продукта"""
    product_data = ProductCreate(
        name="Монитор",
        price=15000.0,
        stock_quantity=5
    )
    product = await product_repository.create(test_session, product_data)
    
    deleted = await product_repository.delete(test_session, product.id)
    assert deleted is True
    
    found_product = await product_repository.get_by_id(test_session, product.id)
    assert found_product is None
