"""
Тесты пагинации

Вопрос 5 из ЛР4: Тест для проверки пагинации товаров
"""
import pytest
from app.schemas.product_schema import ProductCreate


@pytest.mark.asyncio
async def test_product_pagination_first_page(test_session, product_repository):
    """
    Тест пагинации продуктов: первая страница
    
    Проверяемые параметры:
    - count (количество записей на странице)
    - page (номер страницы)
    - Корректность возвращаемых данных
    """
    # Создаем 10 продуктов
    for i in range(10):
        product_data = ProductCreate(
            name=f"Товар {i}",
            price=1000.0 * (i + 1),
            stock_quantity=10 * (i + 1)
        )
        await product_repository.create(test_session, product_data)
    
    # Получаем первую страницу (5 элементов)
    products = await product_repository.get_by_filter(test_session, count=5, page=1)
    
    assert len(products) == 5, "Первая страница должна содержать 5 продуктов"
    assert products[0].name == "Товар 0", "Первый продукт должен быть Товар 0"


@pytest.mark.asyncio
async def test_product_pagination_second_page(test_session, product_repository):
    """
    Тест пагинации: вторая страница
    """
    for i in range(10):
        product_data = ProductCreate(
            name=f"Товар {i}",
            price=1000.0 * (i + 1),
            stock_quantity=10
        )
        await product_repository.create(test_session, product_data)
    
    # Получаем вторую страницу (5 элементов)
    products = await product_repository.get_by_filter(test_session, count=5, page=2)
    
    assert len(products) == 5, "Вторая страница должна содержать 5 продуктов"
    assert products[0].name == "Товар 5", "Первый продукт второй страницы должен быть Товар 5"


@pytest.mark.asyncio
async def test_product_pagination_last_page_partial(test_session, product_repository):
    """
    Тест пагинации: последняя страница с неполным набором данных
    
    Проверяет, что если на последней странице меньше элементов чем count,
    возвращается корректное количество
    """
    # Создаем 12 продуктов
    for i in range(12):
        product_data = ProductCreate(
            name=f"Товар {i}",
            price=1000.0,
            stock_quantity=10
        )
        await product_repository.create(test_session, product_data)
    
    # Получаем третью страницу (должно быть 2 элемента из 12)
    products = await product_repository.get_by_filter(test_session, count=5, page=3)
    
    assert len(products) == 2, "Последняя страница должна содержать 2 продукта"


@pytest.mark.asyncio
async def test_product_pagination_empty_page(test_session, product_repository):
    """
    Тест пагинации: запрос страницы за пределами данных
    """
    # Создаем 5 продуктов
    for i in range(5):
        product_data = ProductCreate(
            name=f"Товар {i}",
            price=1000.0,
            stock_quantity=10
        )
        await product_repository.create(test_session, product_data)
    
    # Запрашиваем 10-ю страницу (должна быть пустой)
    products = await product_repository.get_by_filter(test_session, count=5, page=10)
    
    assert len(products) == 0, "Страница за пределами данных должна быть пустой"


@pytest.mark.asyncio
async def test_product_pagination_total_count(test_session, product_repository):
    """
    Тест: проверка общего количества записей
    
    Важно для правильного отображения пагинации на фронтенде
    """
    # Создаем 15 продуктов
    for i in range(15):
        product_data = ProductCreate(
            name=f"Товар {i}",
            price=1000.0,
            stock_quantity=10
        )
        await product_repository.create(test_session, product_data)
    
    # Получаем общее количество
    total_count = await product_repository.get_total_count(test_session)
    
    assert total_count == 15, "Общее количество должно быть 15"


@pytest.mark.asyncio
async def test_product_pagination_with_zero_count(test_session, product_repository):
    """
    Edge case: попытка получить страницу с нулевым количеством элементов
    """
    for i in range(5):
        product_data = ProductCreate(
            name=f"Товар {i}",
            price=1000.0,
            stock_quantity=10
        )
        await product_repository.create(test_session, product_data)
    
    # count=0 должен вернуть пустой список
    products = await product_repository.get_by_filter(test_session, count=0, page=1)
    
    assert len(products) == 0


@pytest.mark.asyncio
async def test_product_pagination_with_large_count(test_session, product_repository):
    """
    Тест: запрос большого количества элементов на странице
    """
    # Создаем 5 продуктов
    for i in range(5):
        product_data = ProductCreate(
            name=f"Товар {i}",
            price=1000.0,
            stock_quantity=10
        )
        await product_repository.create(test_session, product_data)
    
    # Запрашиваем 100 элементов (больше чем есть)
    products = await product_repository.get_by_filter(test_session, count=100, page=1)
    
    assert len(products) == 5, "Должны вернуться все 5 продуктов"
