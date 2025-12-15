<div style="
  font-family: 'Times New Roman', Times, serif;
  font-size: 14pt;
  line-height: 1.5;
">
<p align="center">
Министерство науки и высшего образования Российской Федерации  
Федеральное государственное автономное образовательное учреждение  
высшего образования  
</p>

<p align="center">
<b>«Уральский федеральный университет<br>
имени первого Президента России Б.Н. Ельцина»</b>
</p>

<p align="center">
Институт радиоэлектроники и информационных технологий – РтФ  
<br>
ШПиАО «Прикладной анализ данных»
</p>

<br>
<br>
<br>

<h2 align="center">ОТЧЕТ</h2>

<p align="center">
по лабораторной работе №4  
</p>

<p align="center">
<b>«Тестирование бэкенд приложения»</b>
</p>

<br>
<br>
<br>

<p align="center">
Преподаватель: Кузьмин Денис Иванович  
</p>

<p align="center">
Обучающийся группы РИМ–150950  
<br>
Козырин Дмитрий Алексеевич
</p>

<br>
<br>
<br>
<br>

<p align="center">
Екатеринбург  
<br>
2025
</p>

## Описание

Проект на основе Litestar (FastAPI-подобный фреймворк) с SQLAlchemy для работы с базой данных.
Реализовано полное тестирование приложения: репозитории, сервисы, API endpoints.


## Установка и запуск

### 1. Установка зависимостей

    pip install -r requirements.txt

### 2. Настройка переменных окружения

Создайте `.env` файл:

    DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/litestar_db

### 3. Запуск приложения

    python app/main.py

Приложение будет доступно по адресу: `http://localhost:8000`

## Тестирование

### Запуск всех тестов

    pytest

### Скрин того, что все тесты приложения пройдены
<img width="1709" height="1040" alt="Снимок экрана 2025-12-16 в 04 29 39" src="https://github.com/user-attachments/assets/c029a895-db62-4e30-a169-f9f5365b8888" />

### Запуск только unit-тестов

    pytest tests/test_repositories/ tests/test_services/

### Запуск только API тестов

    pytest tests/test_routes/

### Запуск с покрытием кода


    pytest --cov=app --cov-report=html

После выполнения откройте `htmlcov/index.html` в браузере для просмотра отчета.

## Особенности реализации

### 1. Pytest Fixtures (Фикстуры)

**Что это**: Переиспользуемые объекты для подготовки тестовой среды.

**Реализованные фикстуры** (в `tests/conftest.py`):

- `engine` - создает in-memory SQLite БД для каждого теста
- `test_session` - предоставляет изолированную сессию БД
- `user_repository`, `product_repository`, и т.д. - репозитории

**Преимущества**:
- Каждый тест получает чистую БД
- Автоматическая очистка после теста
- Изоляция тестов друг от друга

### 2. Модели с поддержкой нескольких продуктов в заказе

**Промежуточная модель `OrderItem`**:

    class OrderItem(Base):
        id = Column(Integer, primary_key=True)
        order_id = Column(Integer, ForeignKey('orders.id'))
        product_id = Column(Integer, ForeignKey('products.id'))
        quantity = Column(Integer)  # Количество товара
        price_at_purchase = Column(Float)  # Цена на момент покупки


**Модель `Product` с количеством на складе**:

    class Product(Base):
        stock_quantity = Column(Integer, default=0)  # Количество на складе

### 3. Тестирование репозиториев

Проверяются все CRUD операции:
- Создание (Create)
- Чтение (Read) - по ID, списком, с фильтрацией
- Обновление (Update)
- Удаление (Delete)

### 4. Тестирование сервисов с Mock

**Mock объекты** позволяют тестировать сервисный слой изолированно:

    @pytest.fixture
    def mock_user_repository():
        return AsyncMock()
    
    mock_user_repository.create.return_value = mock_user

**Преимущества**:
- Не требуется реальная БД
- Тесты выполняются быстрее
- Проверяется только бизнес-логика

### 5. Тестирование API endpoints

Используется `AsyncTestClient` от Litestar:

    async with AsyncTestClient(app=test_app) as client:
        response = await client.post("/users", json={...})
        assert response.status_code == 201

Проверяются:
- HTTP статус-коды
- Валидация данных
- Корректность ответов

### 6. Edge Cases (Граничные случаи)

Тесты для нестандартных ситуаций:

- ❌ Заказ с нулевым/отрицательным количеством
- ❌ Заказ несуществующего продукта
- ❌ Пустой список товаров в заказе
- ⚠️ Заказ товара больше, чем на складе
- ✅ Очень большое количество товара
- ✅ Один продукт несколько раз в заказе

### 7. Изоляция тестов

**Как обеспечивается**:

1. **In-memory SQLite** - каждый тест использует свою БД в памяти
2. **Scope="function"** - фикстуры пересоздаются для каждого теста
3. **Автоматический rollback** - откат транзакций после теста
4. **Параллельное выполнение** - каждый процесс имеет свою среду

## Ответы на вопросы

### 1. Почему используем отдельную тестовую БД?

**Ответ**: 

- **Изоляция**: Тесты не влияют на реальные данные
- **Скорость**: In-memory БД быстрее дисковых
- **Чистота**: Каждый тест начинается с пустой БД
- **Безопасность**: Нельзя случайно удалить production данные

**Проблемы при использовании production БД**:
- Удаление реальных данных пользователей
- Конфликты при параллельном запуске тестов
- Медленное выполнение
- Невозможность тестировать деструктивные операции

### 2. Как работает TestClient в Litestar?

**Ответ**:

`TestClient` создает виртуальное HTTP окружение без запуска реального сервера:

    async with AsyncTestClient(app=test_app) as client:
        response = await client.post("/users", json={...})

**Преимущества**:
- Не нужно запускать сервер
- Быстрое выполнение запросов
- Доступ к внутреннему состоянию приложения
- Автоматическая обработка async/await

### 3. Edge cases для сервиса заказов

**Ответ**: Реализованы тесты в `test_order_edge_cases.py`:

1. Заказ с нулевым/отрицательным количеством
2. Заказ несуществующего продукта
3. Пустой список товаров
4. Количество превышает запасы на складе
5. Несуществующий пользователь/адрес
6. Очень большое количество товара
7. Дублирование продуктов в заказе

### 4. Тестирование отправки email при смене статуса на "shipped"

**Ответ**:


    from unittest.mock import AsyncMock, patch

    @pytest.mark.asyncio
    async def test_order_shipped_sends_email(order_service, mock_order_repository):
        """
        Тест отправки email при смене статуса на shipped
        """
        # Mock email сервиса
        
        with patch('app.services.email_service.send_email') as mock_send_email:
            mock_send_email.return_value = AsyncMock()
            
            # Меняем статус на shipped
            order_data = OrderUpdate(status=OrderStatus.SHIPPED)
            await order_service.update_order_status(1, order_data)
            
            # Проверяем, что email был отправлен
            mock_send_email.assert_called_once()
            args = mock_send_email.call_args
            assert "shipped" in args[0].lower()

**Ключевые моменты**:
- Используем `patch` для замены реального email сервиса
- Проверяем факт вызова функции отправки
- Проверяем параметры вызова (получатель, тема, содержимое)

### 5. Тест для проверки пагинации товаров

**Ответ**: Реализован в `test_pagination.py`

**Проверяемые параметры**:

    @pytest.mark.asyncio
    async def test_product_pagination_parameters(test_session, product_repository):
        # 1. count - количество элементов на странице
        products_page1 = await product_repository.get_by_filter(
            test_session, count=5, page=1
        )
        assert len(products_page1) == 5
        
        # 2. page - номер страницы (начиная с 1)
        products_page2 = await product_repository.get_by_filter(
            test_session, count=5, page=2
        )
        assert products_page2[0].id != products_page1[0].id
        
        # 3. total_count - общее количество записей
        total = await product_repository.get_total_count(test_session)
        assert total == 15
        
        # 4. Последняя страница с неполным набором
        last_page = await product_repository.get_by_filter(
            test_session, count=5, page=3
        )
        assert len(last_page) < 5
        
        # 5. Страница за пределами данных - пустая
        empty_page = await product_repository.get_by_filter(
            test_session, count=5, page=100
        )
        assert len(empty_page) == 0

### 6. Изоляция тестов и её важность

**Ответ**:

**Как обеспечивается**:

1. **Фикстуры с scope="function"**:
   
       @pytest_asyncio.fixture(scope="function")
       async def test_session(engine):
           # Новая сессия для каждого теста


2. **In-memory база данных**:
   
       engine = create_async_engine("sqlite+aiosqlite:///:memory:")
   

3. **Автоматическая очистка**:

        yield session
           await session.rollback()  # Откат изменений
           await session.close()

4. **Пересоздание схемы**:

 
        async with engine.begin() as conn:
           await conn.run_sync(Base.metadata.drop_all)
           await conn.run_sync(Base.metadata.create_all)
  

**Почему это важно**:

- **Независимость**: Результат теста не зависит от других тестов
- **Повторяемость**: Тесты дают одинаковый результат при каждом запуске
- **Отладка**: Легче найти причину падения теста
- **Параллелизм**: Можно запускать тесты параллельно (pytest -n auto)
- **Надежность**: Нет race conditions и конфликтов данных
</div>
