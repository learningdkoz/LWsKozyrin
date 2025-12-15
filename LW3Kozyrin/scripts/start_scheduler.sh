#!/bin/bash
# Скрипт для запуска TaskIQ scheduler
# Scheduler планирует выполнение периодических задач по расписанию

echo "=========================================="
echo "Запуск TaskIQ Scheduler"
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
echo "📅 Запускаем scheduler..."
echo "   - Планировщик будет выполнять задачи по расписанию"
echo "   - Ежедневная генерация отчетов: каждый день в 00:00 UTC"
echo ""

# Запускаем scheduler
# --skip-first-run пропускает первый запуск задач при старте
taskiq scheduler app.scheduler.taskiq_app:scheduler --skip-first-run

echo ""
echo "✅ Scheduler завершил работу"
