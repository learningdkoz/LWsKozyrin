#!/bin/bash
# Скрипт для запуска TaskIQ worker
# Worker обрабатывает задачи из очереди RabbitMQ

echo "=========================================="
echo "Запуск TaskIQ Worker"
echo "=========================================="

# Проверяем наличие переменных окружения
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL не установлена, используется значение по умолчанию"
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/litestar_db"
fi

if [ -z "$RABBITMQ_URL" ]; then
    echo "⚠️  RABBITMQ_URL не установлена, используется значение по умолчанию"
    export RABBITMQ_URL="amqp://guest:guest@localhost:5672/local"
fi

echo "📦 DATABASE_URL: $DATABASE_URL"
echo "🐰 RABBITMQ_URL: $RABBITMQ_URL"
echo ""
echo "🚀 Запускаем worker..."
echo ""

# Запускаем worker
# --fs-discover автоматически находит модули с задачами
taskiq worker app.scheduler.taskiq_app:broker --fs-discover

echo ""
echo "✅ Worker завершил работу"
