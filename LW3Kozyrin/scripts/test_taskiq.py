#!/usr/bin/env python3
"""
Скрипт для тестирования TaskIQ задач
Позволяет вручную запустить генерацию отчета
"""
import asyncio
import sys
from datetime import date, timedelta
import os

# Добавляем корневую директорию в путь для импорта модулей
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.scheduler.taskiq_app import generate_report_for_date, broker


async def test_generate_report():
    """Тестовый запуск генерации отчета"""
    print("=" * 50)
    print("Тестирование TaskIQ: генерация отчета")
    print("=" * 50)

    # Указываем дату для генерации отчета
    # По умолчанию - вчерашний день
    target_date = date.today() - timedelta(days=1)

    print(f"\n📅 Генерируем отчет за: {target_date}")
    print("🔄 Отправляем задачу в очередь...")

    # Запускаем задачу
    task = await generate_report_for_date.kiq(target_date=str(target_date))

    print(f"✅ Задача отправлена!")
    print(f"📋 Task ID: {task.task_id}")
    print("\n💡 Для обработки задачи должен быть запущен worker:")
    print("   bash scripts/start_worker.sh")
    print("\n📊 Проверить результат можно через API:")
    print(f"   GET http://localhost:8000/report/?report_date={target_date}")


async def main():
    """Основная функция"""
    try:
        # Запускаем брокер
        await broker.startup()

        # Выполняем тест
        await test_generate_report()

    finally:
        # Закрываем брокер
        await broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
