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
по лабораторной работе №3  
</p>

<p align="center">
<b>«Внедрение Dependency Injection и SQLAlchemy в Litestar»</b>
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


---

## ИНСТРУКЦИЯ ПО ЗАПУСКУ ПРОЕКТА

### Шаг 1: Настройка базы данных PostgreSQL

Подключитесь к существующей базе данных, изменив переменную окружения `DATABASE_URL`.

### Шаг 2: Установка зависимостей

Клонируйте репозиторий и перейдите в директорию проекта:

```bash
cd путь/к/проекту
```

Установите все необходимые зависимости из файла `requirements.txt`:

```bash
pip install -r requirements.txt
```

Список устанавливаемых пакетов:

    - litestar >= 2.0.0
    - sqlalchemy >= 2.0.0
    - asyncpg >= 0.29.0
    - greenlet >= 3.0.0
    - pydantic >= 2.0.0
    - pydantic[email] >= 2.0.0
    - uvicorn >= 0.24.0
    - python-dotenv >= 1.0.0

### Шаг 3: Настройка переменных окружения (опционально)

По умолчанию приложение использует следующую строку подключения к БД:

```
postgresql+asyncpg://postgres:viking676@localhost:5432/litestar_db
```

Если нужно изменить параметры подключения, создайте файл `.env` в корне проекта:

```env
DATABASE_URL=postgresql+asyncpg://ваш_пользователь:ваш_пароль@localhost:5432/ваша_бд
```

### Шаг 4: Запуск приложения

Запустите приложение командой:

```bash
python -m app.main
```

Или альтернативно через uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Параметр `--reload` включает автоматическую перезагрузку при изменении кода (полезно для разработки).

### Шаг 5: Проверка работоспособности

После успешного запуска приложение будет доступно по адресу: `http://localhost:8000`

Автоматически созданная документация API доступна по адресу:
- Swagger UI: `http://localhost:8000/schema`
- OpenAPI Schema: `http://localhost:8000/schema/openapi.json`

### Доступные эндпоинты

- `GET /users` - получить список пользователей с пагинацией
- `GET /users/{user_id}` - получить пользователя по ID
- `POST /users` - создать нового пользователя
- `PUT /users/{user_id}` - обновить данные пользователя
- `DELETE /users/{user_id}` - удалить пользователя

### Пример создания пользователя

```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User"
  }'
```

---

## 1. ЦЕЛЬ РАБОТЫ

Освоить принципы Dependency Injection и интеграцию SQLAlchemy ORM в веб-приложении на базе фреймворка Litestar, реализовав CRUD-операции для управления пользователями.

---

## 2. ОПИСАНИЕ ЗАДАЧИ

В рамках лабораторной работы необходимо было реализовать полнофункциональное веб-приложение для управления пользователями с использованием трехслойной архитектуры:

1. **Слой Repository** – для работы с базой данных (создание, чтение, обновление, удаление пользователей)
2. **Слой Service** – для реализации бизнес-логики
3. **Слой Controller** – для обработки HTTP-запросов и формирования ответов

Приложение должно поддерживать следующие операции:
- Получение пользователя по ID
- Получение списка пользователей с пагинацией
- Создание нового пользователя
- Обновление данных пользователя
- Удаление пользователя

**Задание со звездочкой:** При запросе списка пользователей возвращать также общее количество пользователей в базе данных.

---

## 3. ХОД ВЫПОЛНЕНИЯ

### 3.1. Модель данных (app/models/user.py)

Была создана модель `User` для представления пользователя в базе данных с использованием SQLAlchemy ORM:

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Модель пользователя для базы данных"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, 
                       onupdate=datetime.utcnow, nullable=False)
```

**Описание:** Модель содержит основные поля пользователя, включая уникальные username и email с индексами для быстрого поиска, а также временные метки создания и обновления записи.

---

### 3.2. Схемы данных (app/schemas/user_schema.py)

Созданы Pydantic-схемы для валидации входных и выходных данных:

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)

class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)

class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """Схема для ответа со списком пользователей"""
    users: list[UserResponse]
    total_count: int
```

**Описание:** Схемы обеспечивают валидацию данных на уровне API, разделяя входные данные (Create/Update) и выходные (Response). Схема `UserListResponse` реализует задание со звездочкой, включая поле `total_count`.

---

### 3.3. Репозиторий (app/repositories/user_repository.py)

Реализован слой работы с базой данных:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserUpdate
from typing import Optional

class UserRepository:
    """Репозиторий для работы с пользователями в базе данных"""

    async def get_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_filter(
        self, 
        session: AsyncSession, 
        count: int = 10, 
        page: int = 1, 
        **kwargs
    ) -> list[User]:
        """Получить список пользователей с пагинацией"""
        query = select(User)
        
        # Применяем фильтры
        if "username" in kwargs and kwargs["username"]:
            query = query.where(User.username == kwargs["username"])
        if "email" in kwargs and kwargs["email"]:
            query = query.where(User.email == kwargs["email"])
        
        # Пагинация
        offset = (page - 1) * count
        query = query.offset(offset).limit(count)
        
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_total_count(self, session: AsyncSession) -> int:
        """Получить общее количество пользователей"""
        result = await session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def create(self, session: AsyncSession, user_data: UserCreate) -> User:
        """Создать нового пользователя"""
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update(
        self, 
        session: AsyncSession, 
        user_id: int, 
        user_data: UserUpdate
    ) -> Optional[User]:
        """Обновить данные пользователя"""
        user = await self.get_by_id(session, user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await session.commit()
        await session.refresh(user)
        return user

    async def delete(self, session: AsyncSession, user_id: int) -> bool:
        """Удалить пользователя"""
        user = await self.get_by_id(session, user_id)
        if not user:
            return False
        
        await session.delete(user)
        await session.commit()
        return True
```

**Описание:** Репозиторий инкапсулирует всю логику работы с базой данных. Метод `get_total_count()` добавлен для выполнения задания со звездочкой. Все методы принимают сессию как параметр, что обеспечивает гибкость управления транзакциями.

---

### 3.4. Сервисный слой (app/services/user_service.py)

Реализован слой бизнес-логики:

```python
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

class UserService:
    """Сервисный слой для работы с пользователями"""
    
    def __init__(self, user_repository: UserRepository, db_session: AsyncSession):
        self.user_repository = user_repository
        self.db_session = db_session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return await self.user_repository.get_by_id(self.db_session, user_id)

    async def get_by_filter(
        self, 
        count: int = 10, 
        page: int = 1, 
        **kwargs
    ) -> list[User]:
        """Получить список пользователей с фильтрацией"""
        return await self.user_repository.get_by_filter(
            self.db_session, count, page, **kwargs
        )

    async def get_total_count(self) -> int:
        """Получить общее количество пользователей"""
        return await self.user_repository.get_total_count(self.db_session)

    async def create(self, user_data: UserCreate) -> User:
        """Создать нового пользователя"""
        return await self.user_repository.create(self.db_session, user_data)

    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Обновить данные пользователя"""
        return await self.user_repository.update(self.db_session, user_id, user_data)

    async def delete(self, user_id: int) -> bool:
        """Удалить пользователя"""
        return await self.user_repository.delete(self.db_session, user_id)
```

**Описание:** Сервисный слой служит посредником между контроллером и репозиторием. В текущей реализации он выполняет роль прокси, но предоставляет место для добавления бизнес-логики в будущем.

---

### 3.5. Контроллер (app/controllers/user_controller.py)

Реализован слой обработки HTTP-запросов:

```python
from litestar import Controller, get, post, put, delete
from litestar.di import Provide
from litestar.params import Parameter
from litestar.exceptions import NotFoundException
from app.services.user_service import UserService
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse, UserListResponse
from typing import List

class UserController(Controller):
    """Контроллер для управления пользователями"""
    path = "/users"

    @get("/{user_id:int}")
    async def get_user_by_id(
        self,
        user_service: UserService,
        user_id: int = Parameter(gt=0),
    ) -> UserResponse:
        """Получить пользователя по ID"""
        user = await user_service.get_by_id(user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)

    @get()
    async def get_all_users(
        self,
        user_service: UserService,
        count: int = Parameter(10, gt=0, le=100),
        page: int = Parameter(1, gt=0),
    ) -> UserListResponse:
        """Получить список пользователей с пагинацией"""
        users = await user_service.get_by_filter(count=count, page=page)
        total_count = await user_service.get_total_count()
        
        return UserListResponse(
            users=[UserResponse.model_validate(user) for user in users],
            total_count=total_count
        )

    @post()
    async def create_user(
        self,
        user_service: UserService,
        data: UserCreate,
    ) -> UserResponse:
        """Создать нового пользователя"""
        user = await user_service.create(data)
        return UserResponse.model_validate(user)

    @delete("/{user_id:int}", status_code=200)
    async def delete_user(
        self,
        user_service: UserService,
        user_id: int = Parameter(gt=0),
    ) -> dict:
        """Удалить пользователя"""
        deleted = await user_service.delete(user_id)
        if not deleted:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return {"message": f"User with ID {user_id} successfully deleted"}

    @put("/{user_id:int}")
    async def update_user(
        self,
        user_service: UserService,
        user_id: int = Parameter(gt=0),
        data: UserUpdate = None,
    ) -> UserResponse:
        """Обновить данные пользователя"""
        user = await user_service.update(user_id, data)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)
```

**Описание:** Контроллер определяет эндпоинты API и обрабатывает HTTP-запросы. Метод `get_all_users()` возвращает `UserListResponse` с общим количеством пользователей согласно заданию со звездочкой.

---

### 3.6. Главное приложение (app/main.py)

Настроено главное приложение с Dependency Injection:

```python
import os
from litestar import Litestar
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.controllers.user_controller import UserController
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.models.user import Base

# Настройка базы данных
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:viking676@localhost:5432/litestar_db"
)

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async_session_factory = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def provide_db_session() -> AsyncSession:
    """Провайдер сессии базы данных"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def provide_user_repository(db_session: AsyncSession) -> UserRepository:
    """Провайдер репозитория пользователей"""
    return UserRepository()

async def provide_user_service(
    user_repository: UserRepository,
    db_session: AsyncSession
) -> UserService:
    """Провайдер сервиса пользователей"""
    return UserService(user_repository, db_session)

async def init_database() -> None:
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = Litestar(
    route_handlers=[UserController],
    dependencies={
        "db_session": Provide(provide_db_session),
        "user_repository": Provide(provide_user_repository),
        "user_service": Provide(provide_user_service),
    },
    on_startup=[init_database],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Описание:** В `main.py` настроены провайдеры зависимостей для автоматического внедрения сессии БД, репозитория и сервиса. При запуске приложения автоматически создаются все необходимые таблицы в базе данных.

---

## 4. ССЫЛКА НА РЕПОЗИТОРИЙ

GitHub: [указать ссылку на репозиторий]

Теги:
- `lab_2` – последний коммит лабораторной работы 2
- `lab_3` – завершение лабораторной работы 3

---

## 5. ОТВЕТЫ НА ВОПРОСЫ

### Вопрос 1: Объясните принцип Dependency Injection (DI) своими словами

**Ответ:**

Dependency Injection (внедрение зависимостей) – это принцип проектирования, при котором объект не создает свои зависимости самостоятельно, а получает их извне. Это решает проблему сильной связанности компонентов и упрощает тестирование.

**Проблема, которую решает DI:**
- Жесткая связь между компонентами – когда класс создает свои зависимости внутри себя, его сложно тестировать и изменять
- Сложность замены реализации – невозможно легко подменить зависимость на mock-объект для тестирования

**Преимущества DI:**
- Упрощение тестирования – можно легко подставить mock-объекты вместо реальных зависимостей
- Гибкость – легко заменить одну реализацию на другую без изменения кода класса
- Разделение ответственности – объект не отвечает за создание своих зависимостей
- Переиспользование кода – один и тот же сервис может использоваться в разных контроллерах

В нашем приложении DI реализован через провайдеры Litestar, которые автоматически создают и внедряют экземпляры `UserRepository` и `UserService` в методы контроллера.

---

### Вопрос 2: Обязанности трех слоев приложения

**Ответ:**

**Repository (Репозиторий):**
- Работа с базой данных (SQL-запросы)
- Маппинг данных между ORM-моделями и БД
- Изоляция логики доступа к данным
- Не содержит бизнес-логики

**Service (Сервис):**
- Бизнес-логика приложения
- Валидация на уровне бизнес-правил
- Координация работы нескольких репозиториев
- Интеграция с внешними системами (email, платежи и т.д.)

**Controller (Контроллер):**
- Обработка HTTP-запросов
- Валидация входных данных (параметры, тело запроса)
- Формирование HTTP-ответов
- Управление HTTP-статусами и заголовками

**Почему это хорошая практика:**
- **Разделение ответственности** – каждый слой решает свою задачу
- **Тестируемость** – можно тестировать каждый слой независимо
- **Переиспользование** – репозитории и сервисы можно использовать в разных контроллерах
- **Поддерживаемость** – изменения в одном слое не затрагивают другие

**Если объединить Repository и Controller:**
- Нарушится принцип единственной ответственности
- Контроллер станет зависимым от конкретной реализации БД
- Невозможно будет переиспользовать логику работы с БД
- Усложнится тестирование – придется мокать БД в тестах контроллера
- Замена БД потребует изменения всех контроллеров

---

### Вопрос 3: Жизненный цикл зависимости в Litestar

**Ответ:**

При обработке одного HTTP-запроса происходит следующее:

1. **Запрос поступает** на эндпоинт контроллера
2. **Litestar анализирует зависимости** метода-обработчика
3. **Вызывается `provide_db_session()`:**
   - Создается новая асинхронная сессия через `async_session_factory()`
   - Сессия передается через `yield` (генератор)
4. **Вызывается `provide_user_repository(db_session)`:**
   - Получает созданную сессию как аргумент
   - Создает экземпляр `UserRepository`
5. **Вызывается `provide_user_service(user_repository, db_session)`:**
   - Получает репозиторий и сессию
   - Создает экземпляр `UserService`
6. **Метод контроллера выполняется** с внедренными зависимостями
7. **После завершения метода:**
   - Выполняется код после `yield` в `provide_db_session()`
   - В блоке `finally` вызывается `session.close()` – **сессия уничтожается**
   - Если произошла ошибка, выполняется `session.rollback()`

**Важно:** Каждый запрос получает свою собственную сессию БД, что обеспечивает изоляцию транзакций.

---

### Вопрос 4: Что такое async/await и зачем они используются

**Ответ:**

**async/await** – это синтаксис для работы с асинхронным кодом в Python.

**Принцип работы:**
- `async` перед функцией делает её корутиной (асинхронной функцией)
- `await` приостанавливает выполнение корутины, пока не завершится асинхронная операция
- Во время ожидания поток управления передается другим задачам

**Зачем используется в приложении:**

1. **Неблокирующие операции с БД:**
   - Когда выполняется SQL-запрос, поток не блокируется
   - В это время могут обрабатываться другие HTTP-запросы

2. **Повышение производительности:**
   - Один процесс может обрабатывать тысячи одновременных запросов
   - Не нужно создавать отдельный поток для каждого запроса

3. **Эффективное использование ресурсов:**
   - Время ожидания ответа от БД используется для обработки других запросов
   - Меньше потребление памяти по сравнению с многопоточностью

**Пример влияния на производительность:**
- **Синхронный подход:** 1000 запросов × 50ms (время БД) = 50 секунд последовательно
- **Асинхронный подход:** 1000 запросов могут выполняться параллельно ≈ 50-100ms

---

### Вопрос 5: Почему session передается как аргумент в UserRepository

**Ответ:**

**Почему session передается как параметр:**

1. **Управление транзакциями на верхнем уровне:**
   - Позволяет контролировать границы транзакции извне репозитория
   - Можно выполнить несколько операций в одной транзакции

2. **Гибкость:**
   - Можно использовать одну сессию для нескольких операций
   - Можно откатить всю группу операций при ошибке

3. **Тестируемость:**
   - Легко подменить сессию на mock-объект в тестах
   - Можно использовать in-memory БД для тестов

**Почему не создавать session внутри репозитория:**

1. **Потеря контроля над транзакциями:**
   - Каждый метод создавал бы свою сессию и транзакцию
   - Невозможно было бы атомарно выполнить несколько операций

2. **Проблемы с производительностью:**
   - Создание новой сессии для каждой операции дорого
   - Нельзя использовать кеширование на уровне сессии

**Кто вызывает commit/rollback:**

- **commit()** вызывается в методах репозитория после успешной операции записи (create, update, delete)
- **rollback()** вызывается в провайдере `provide_db_session()` в блоке `except` при ошибке
- Это обеспечивает автоматический откат всех изменений при любой ошибке в обработке запроса

---

### Вопрос 6: Для чего используется пагинация (count и page)

**Ответ:**

Пагинация необходима для эффективной работы с большими объемами данных:

**Проблемы без пагинации:**
1. **Производительность:**
   - Запрос всех записей из БД может занять много времени
   - Передача большого объема данных по сети замедляет отклик

2. **Память:**
   - Загрузка миллионов записей может привести к нехватке памяти
   - На клиенте невозможно отобразить все данные сразу

3. **Пользовательский опыт:**
   - Пользователь не может эффективно работать с тысячами записей на одной странице

**Как работает пагинация:**
- `count` – количество записей на странице (например, 10)
- `page` – номер страницы (начиная с 1)
- `offset = (page - 1) * count` – сдвиг от начала выборки

**Пример:**
- Страница 1: записи 1-10 (offset=0, limit=10)
- Страница 2: записи 11-20 (offset=10, limit=10)
- Страница 3: записи 21-30 (offset=20, limit=10)

**Дополнительные преимущества:**
- Кеширование страниц на клиенте
- Возможность прямой навигации к нужной странице
- Снижение нагрузки на сервер и БД

---

### Вопрос 7: Пример бизнес-логики в сервисном слое

**Ответ:**

В текущей реализации `UserService` действительно является прокси для `UserRepository`. Примеры бизнес-логики, которую можно добавить:

**1. Проверка уникальности email перед созданием:**
```python
async def create(self, user_data: UserCreate) -> User:
    # Проверяем, не существует ли пользователь с таким email
    existing_users = await self.user_repository.get_by_filter(
        self.db_session, count=1, page=1, email=user_data.email
    )
    if existing_users:
        raise ValueError(f"User with email {user_data.email} already exists")
    
    return await self.user_repository.create(self.db_session, user_data)
```

**2. Хеширование пароля (если добавить поле password):**
```python
import bcrypt

async def create(self, user_data: UserCreate) -> User:
    # Хешируем пароль перед сохранением
    hashed_password = bcrypt.hashpw(
        user_data.password.encode('utf-8'), 
        bcrypt.gensalt()
    )
    user_data.password = hashed_password.decode('utf-8')
    
    return await self.user_repository.create(self.db_session, user_data)
```

**3. Отправка приветственного письма:**
```python
async def create(self, user_data: UserCreate) -> User:
    # Создаем пользователя
    user = await self.user_repository.create(self.db_session, user_data)
    
    # Отправляем приветственное письмо
    await self.email_service.send_welcome_email(
        to=user.email,
        username=user.username
    )
    
    return user
```

**4. Логирование действий пользователя:**
```python
async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
    # Получаем старые данные
    old_user = await self.user_repository.get_by_id(self.db_session, user_id)
    
    # Обновляем пользователя
    updated_user = await self.user_repository.update(
        self.db_session, user_id, user_data
    )
    
    # Логируем изменения
    await self.audit_service.log_user_update(
        user_id=user_id,
        old_data=old_user,
        new_data=updated_user,
        changed_at=datetime.utcnow()
    )
    
    return updated_user
```

**5. Проверка бизнес-правил при удалении:**
```python
async def delete(self, user_id: int) -> bool:
    # Проверяем, есть ли у пользователя активные заказы
    active_orders = await self.order_repository.get_active_orders_count(
        self.db_session, user_id
    )
    
    if active_orders > 0:
        raise ValueError(
            f"Cannot delete user with {active_orders} active orders"
        )
    
    return await self.user_repository.delete(self.db_session, user_id)
```

Эти примеры показывают, что сервисный слой – это место для бизнес-логики, валидации, интеграций и координации работы нескольких репозиториев.

---

### Вопрос 8: HTTP-статусы для каждого эндпоинта

**Ответ:**

**GET /users/{user_id} – Получение пользователя по ID**

| Сценарий | HTTP-статус | Обоснование |
|----------|-------------|-------------|
| Пользователь найден | 200 OK | Запрос выполнен успешно, данные возвращены |
| Пользователь не найден | 404 Not Found | Ресурс с указанным ID не существует |
| Некорректный ID (например, отрицательный) | 400 Bad Request | Клиент передал некорректные данные |
| Ошибка сервера/БД | 500 Internal Server Error | Внутренняя ошибка сервера |

**GET /users – Получение списка пользователей**

| Сценарий | HTTP-статус | Обоснование |
|----------|-------------|-------------|
| Список получен (даже если пустой) | 200 OK | Запрос выполнен успешно |
| Некорректные параметры пагинации | 400 Bad Request | Неверные значения count или page |
| Ошибка сервера/БД | 500 Internal Server Error | Внутренняя ошибка сервера |

**POST /users – Создание пользователя**

| Сценарий | HTTP-статус | Обоснование |
|----------|-------------|-------------|
| Пользователь создан | 201 Created | Новый ресурс успешно создан |
| Невалидные данные | 400 Bad Request | Не прошла валидация (некорректный email и т.д.) |
| Пользователь уже существует (дубликат) | 409 Conflict | Конфликт с существующим ресурсом |
| Ошибка сервера/БД | 500 Internal Server Error | Внутренняя ошибка сервера |

**PUT /users/{user_id} – Обновление пользователя**

| Сценарий | HTTP-статус | Обоснование |
|----------|-------------|-------------|
| Пользователь обновлен | 200 OK | Ресурс успешно изменен, данные возвращены |
| Пользователь не найден | 404 Not Found | Ресурс с указанным ID не существует |
| Невалидные данные | 400 Bad Request | Не прошла валидация новых данных |
| Конфликт (например, email уже занят) | 409 Conflict | Нарушение уникальности |
| Ошибка сервера/БД | 500 Internal Server Error | Внутренняя ошибка сервера |

**DELETE /users/{user_id} – Удаление пользователя**

| Сценарий | HTTP-статус | Обоснование |
|----------|-------------|-------------|
| Пользователь удален | 200 OK или 204 No Content | Ресурс успешно удален. 204 если нет тела ответа |
| Пользователь не найден | 404 Not Found | Ресурс с указанным ID не существует |
| Некорректный ID | 400 Bad Request | Клиент передал некорректный ID |
| Ошибка сервера/БД | 500 Internal Server Error | Внутренняя ошибка сервера |

**Примечание:** В нашей реализации DELETE возвращает 200 OK с сообщением об успешном удалении. Альтернативный вариант – возвращать 204 No Content без тела ответа.

---

## 6. ВЫВОД

В ходе выполнения лабораторной работы была успешно реализована трехслойная архитектура веб-приложения с использованием фреймворка Litestar и ORM SQLAlchemy. Было освоено применение паттерна Dependency Injection для управления зависимостями, что обеспечило слабую связанность компонентов и упростило тестирование.

Реализованное приложение поддерживает полный набор CRUD-операций для управления пользователями: создание, чтение, обновление и удаление. Использование асинхронного программирования (async/await) обеспечило высокую производительность при работе с базой данных.

Трехслойная архитектура (Repository-Service-Controller) продемонстрировала свои преимущества:
- Четкое разделение ответственности между компонентами
- Возможность независимого тестирования каждого слоя
- Гибкость при изменении реализации отдельных компонентов
- Переиспользование логики работы с данными

Дополнительно было выполнено задание со звездочкой: при запросе списка пользователей возвращается общее количество пользователей в базе данных, что необходимо для реализации пагинации на клиентской стороне.

Полученные знания и навыки являются фундаментальными для разработки современных веб-приложений и могут быть применены при работе с другими фреймворками и технологиями.

</div>
