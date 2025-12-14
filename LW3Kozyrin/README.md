# Лабораторная работа 3: Внедрение Dependency Injection и SQLAlchemy в Litestar

## Описание

Реализация CRUD API для управления пользователями с использованием:
- **Litestar** - современный асинхронный веб-фреймворк
- **SQLAlchemy** - ORM для работы с базой данных
- **Dependency Injection** - паттерн для управления зависимостями
- **Трехслойная архитектура** - разделение на Controller, Service, Repository

## Структура проекта

\`\`\`
app/
├── controllers/
│   └── user_controller.py    # HTTP endpoints
├── services/
│   └── user_service.py        # Бизнес-логика
├── repositories/
│   └── user_repository.py     # Работа с БД
├── models/
│   └── user.py                # SQLAlchemy модели
├── schemas/
│   └── user_schema.py         # Pydantic схемы
└── main.py                    # Точка входа приложения
\`\`\`

## Установка и запуск

### 1. Установка зависимостей

\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 2. Настройка базы данных PostgreSQL

Установите PostgreSQL и создайте базу данных:

\`\`\`bash
# Подключитесь к PostgreSQL
psql -U postgres

# Создайте базу данных
CREATE DATABASE litestar_db;

# Создайте пользователя
CREATE USER user WITH PASSWORD 'password';

# Предоставьте права
GRANT ALL PRIVILEGES ON DATABASE litestar_db TO user;
\`\`\`

### 3. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и измените параметры подключения:

\`\`\`bash
cp .env.example .env
\`\`\`

Отредактируйте `.env`:
\`\`\`
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/litestar_db
\`\`\`

### 4. Запуск приложения

\`\`\`bash
python app/main.py
\`\`\`

Или с помощью uvicorn:

\`\`\`bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

## Использование API

### Документация API

После запуска приложения документация доступна по адресу:
- Swagger UI: http://localhost:8000/schema/swagger
- OpenAPI Schema: http://localhost:8000/schema/openapi.json

### Примеры запросов

#### 1. Создать пользователя (POST /users)

\`\`\`bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john.doe@example.com",
    "full_name": "John Doe"
  }'
\`\`\`

#### 2. Получить пользователя по ID (GET /users/{user_id})

\`\`\`bash
curl http://localhost:8000/users/1
\`\`\`

#### 3. Получить список пользователей с пагинацией (GET /users)

\`\`\`bash
# Получить первые 10 пользователей (страница 1)
curl "http://localhost:8000/users?count=10&page=1"

# Получить следующие 10 пользователей (страница 2)
curl "http://localhost:8000/users?count=10&page=2"
\`\`\`

#### 4. Обновить пользователя (PUT /users/{user_id})

\`\`\`bash
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.updated@example.com",
    "full_name": "John Updated"
  }'
\`\`\`

#### 5. Удалить пользователя (DELETE /users/{user_id})

\`\`\`bash
curl -X DELETE http://localhost:8000/users/1
\`\`\`

## Работа с Git

### Создание тега для лабораторной работы 2

Перед началом работы создайте тег для предыдущей лабораторной:

\`\`\`bash
git tag lab_2
git push origin lab_2
\`\`\`

### Завершение лабораторной работы 3

После завершения работы создайте тег:

\`\`\`bash
git add .
git commit -m "Completed lab 3: Dependency Injection and SQLAlchemy"
git tag lab_3
git push origin main
git push origin lab_3
\`\`\`

## Архитектура приложения

### Трехслойная архитектура

1. **Controller (Контроллер)** - `user_controller.py`
   - Обрабатывает HTTP-запросы
   - Валидирует входные данные
   - Возвращает HTTP-ответы

2. **Service (Сервис)** - `user_service.py`
   - Содержит бизнес-логику
   - Координирует работу репозиториев
   - Может интегрироваться с внешними системами

3. **Repository (Репозиторий)** - `user_repository.py`
   - Работает с базой данных
   - Выполняет CRUD операции
   - Изолирует логику работы с БД

### Dependency Injection

Приложение использует встроенный DI контейнер Litestar:

- `provide_db_session()` - создает сессию БД для каждого запроса
- `provide_user_repository()` - создает экземпляр репозитория
- `provide_user_service()` - создает экземпляр сервиса с зависимостями

### Жизненный цикл запроса

1. Приходит HTTP-запрос
2. Litestar создает сессию БД через `provide_db_session()`
3. Создается репозиторий через `provide_user_repository()`
4. Создается сервис через `provide_user_service()`
5. Контроллер обрабатывает запрос
6. Сессия БД автоматически закрывается

## Задание со звездочкой ⭐

Реализовано в методе `get_all_users()`:
- Возвращает не только список пользователей, но и общее количество
- Используется схема `UserListResponse` с полями `users` и `total_count`
- Помогает реализовать пагинацию на клиенте

## HTTP статусы

- **200 OK** - Успешный GET/PUT
- **201 Created** - Успешный POST (создание)
- **204 No Content** - Успешный DELETE
- **400 Bad Request** - Невалидные данные
- **404 Not Found** - Ресурс не найден
- **500 Internal Server Error** - Ошибка сервера
