#!/bin/bash

# Скрипт запуска приложения в Docker контейнере
# Выполняет инициализацию базы данных и запускает приложение

set -e  # Прерывание выполнения при ошибке

echo "===================================="
echo "Starting Litestar Application"
echo "===================================="

# Ожидание готовности базы данных (опционально)
echo "Waiting for database to be ready..."
sleep 5

# Здесь можно добавить команды для миграций БД, например:
# echo "Running database migrations..."
# alembic upgrade head

# Запуск приложения с помощью Uvicorn
echo "Starting Uvicorn server..."
exec uvicorn app.main:app \
    --host ${HOST:-0.0.0.0} \
    --port ${PORT:-8000} \
    --reload \
    --log-level ${LOG_LEVEL:-info}
