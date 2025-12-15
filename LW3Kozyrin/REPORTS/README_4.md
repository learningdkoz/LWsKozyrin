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


### Ход выполнения
1. Подготовка тестового окружения

Для тестирования была настроена отдельная тестовая база данных SQLite in-memory. Это позволило запускать тесты быстро и изолированно, не затрагивая основную базу данных проекта.

Были созданы pytest-фикстуры для:

-инициализации тестовой базы данных
-подключения репозиториев
-очистки данных после выполнения тестов

Пример фикстуры создания движка: 

    @pytest_asyncio.fixture(scope="function")
    async def engine():
        """
        Фикстура для создания тестового движка базы данных
    
        Использует SQLite in-memory для изоляции тестов и быстрой работы.
        Каждый тест получает чистую базу данных.
    
        Yields:
            AsyncEngine: Асинхронный движок базы данных
        """
        # Создаем in-memory SQLite БД для тестов
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False  # Отключаем логирование SQL для чистоты вывода тестов
        )
    
        # Создаем все таблицы
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
        yield engine
    
        # Очищаем после теста
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

Фикстуры использовались с областью видимости function, чтобы каждый тест запускался в чистом окружении.

2. Тестирование репозиториев

<img width="1685" height="475" alt="Снимок экрана 2025-12-16 в 04 57 41" src="https://github.com/user-attachments/assets/d553b6e1-94be-4630-8867-c210382beb2d" />

На первом этапе были написаны тесты для репозитория пользователей:

-создание пользователя
-получение пользователя по id
-обновление данных пользователя
–удаление пользователя
–получение списка пользователей

Пример тестирования корректного создания пользователя:

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

Далее аналогичные тесты были реализованы для репозиториев продукции и заказов. При тестировании заказов учитывался случай, когда в одном заказе может быть несколько продуктов.
Также была проверена корректность работы с количеством товара на складе.

3. Тестирование сервисного слоя

<img width="1683" height="269" alt="Снимок экрана 2025-12-16 в 04 58 24" src="https://github.com/user-attachments/assets/bb32817b-9c87-4250-8a12-4af170505188" />

Для тестирования сервисного слоя использовались mock-объекты. Это позволило проверить бизнес-логику сервисов без реального взаимодействия с базой данных.

С помощью mock:

-подменялись репозитории

-проверялись сценарии успешного выполнения операций
–тестировалась обработка ошибок

Пример получения пользователя по идентификатора:

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

Таким образом удалось изолировать сервисный слой и проверить его логику отдельно от остальных компонентов приложения.

4. Тестирование API

<img width="1688" height="274" alt="Снимок экрана 2025-12-16 в 04 59 03" src="https://github.com/user-attachments/assets/9dc143ac-087e-4f6d-94ca-7706522f6218" />

На следующем этапе было протестировано API приложения. Для этого использовался TestClient, который позволяет отправлять запросы к эндпоинтам без запуска реального сервера.

Были написаны тесты для:

-создания пользователей
-получения списка пользователей
-обновления данных
-удаления сущностей
-работы эндпоинтов заказов и продукции

Каждый тест проверял HTTP-статус ответа и корректность возвращаемых данных.


5. Запуск тестов и анализ покрытия

Тесты запускались следующими командами:

-запуск всех тестов
-запуск unit-тестов
-запуск API-тестов
-запуск тестов с покрытием кода

Также был настроен файл pyproject.toml для конфигурации pytest, включая пути к тестам и дополнительные параметры запуска.

Код toml файла:

    [tool.pytest.ini_options]
    testpaths = ["tests"]
    asyncio_mode = "auto"
    addopts = "--verbose --color=yes"
    pythonpath = ["."]
    
    [tool.coverage.run]
    source = ["app"]
    omit = ["tests/*", "*/migrations/*"]
    
    [tool.coverage.report]
    exclude_lines = [
        "pragma: no cover",
        "def __repr__",
        "raise AssertionError",
        "raise NotImplementedError",
        "if __name__ == .__main__.:",
    ]

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
