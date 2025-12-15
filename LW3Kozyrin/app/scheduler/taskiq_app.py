"""
Модуль планировщика задач TaskIQ
"""
import os
from datetime import datetime, date, timedelta
from taskiq import TaskiqScheduler
from taskiq_aio_pika import AioPikaBroker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, func
from app.models.order import Order, OrderItem
from app.models.report import Report
from app.schemas.report_schema import ReportCreate
from app.repositories.report_repository import ReportRepository

# Получаем URL для RabbitMQ из переменных окружения
RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://guest:guest@localhost:5672/local"
)

# Получаем URL для базы данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/litestar_db"
)

# Создаем брокер TaskIQ на основе RabbitMQ
broker = AioPikaBroker(RABBITMQ_URL)

# Создаем планировщик
scheduler = TaskiqScheduler(broker, [])


# Создаем движок и фабрику сессий для TaskIQ
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@broker.task(schedule=[{"cron": "0 0 * * *"}])
async def generate_daily_report():
    """
    Задача для генерации ежедневного отчета по заказам
    Запускается каждый день в 00:00 по UTC

    Формирует отчет за предыдущий день:
    - Находит все заказы, созданные вчера
    - Для каждого заказа подсчитывает количество продуктов
    - Сохраняет информацию в таблицу reports
    """
    # Дата вчерашнего дня (за который формируем отчет)
    yesterday = date.today() - timedelta(days=1)

    print(f"[TaskIQ] Начало генерации отчета за {yesterday}")

    async with async_session_factory() as session:
        # Получаем все заказы за вчерашний день
        start_date = datetime.combine(yesterday, datetime.min.time())
        end_date = datetime.combine(yesterday + timedelta(days=1), datetime.min.time())

        result = await session.execute(
            select(Order).where(
                Order.created_at >= start_date,
                Order.created_at < end_date
            )
        )
        orders = result.scalars().all()

        if not orders:
            print(f"[TaskIQ] Заказов за {yesterday} не найдено")
            return {
                "status": "success",
                "date": str(yesterday),
                "reports_created": 0,
                "message": "Нет заказов за указанную дату"
            }

        report_repo = ReportRepository()

        # Удаляем старые отчеты за эту дату (если есть)
        deleted_count = await report_repo.delete_by_date(session, yesterday)
        if deleted_count > 0:
            print(f"[TaskIQ] Удалено старых отчетов: {deleted_count}")

        # Создаем отчет для каждого заказа
        reports_created = 0
        for order in orders:
            # Подсчитываем количество продуктов в заказе
            items_result = await session.execute(
                select(func.sum(OrderItem.quantity))
                .where(OrderItem.order_id == order.id)
            )
            total_products = items_result.scalar() or 0

            # Создаем запись в отчете только если есть продукты
            if total_products > 0:
                report_data = ReportCreate(
                    report_at=yesterday,
                    order_id=order.id,
                    count_product=total_products
                )
                await report_repo.create(session, report_data)
                reports_created += 1

        print(f"[TaskIQ] Отчет за {yesterday} сформирован. Создано записей: {reports_created}")

        return {
            "status": "success",
            "date": str(yesterday),
            "reports_created": reports_created,
            "orders_processed": len(orders)
        }


@broker.task
async def generate_report_for_date(target_date: str):
    """
    Задача для генерации отчета за конкретную дату
    Можно вызвать вручную через API

    Args:
        target_date: Дата в формате YYYY-MM-DD
    """
    try:
        report_date = date.fromisoformat(target_date)
    except ValueError as e:
        print(f"[TaskIQ] Ошибка формата даты: {e}")
        return {
            "status": "error",
            "message": f"Неверный формат даты: {target_date}"
        }

    print(f"[TaskIQ] Начало генерации отчета за {report_date}")

    async with async_session_factory() as session:
        # Получаем все заказы за указанный день
        start_date = datetime.combine(report_date, datetime.min.time())
        end_date = datetime.combine(report_date + timedelta(days=1), datetime.min.time())

        result = await session.execute(
            select(Order).where(
                Order.created_at >= start_date,
                Order.created_at < end_date
            )
        )
        orders = result.scalars().all()

        if not orders:
            print(f"[TaskIQ] Заказов за {report_date} не найдено")
            return {
                "status": "success",
                "date": str(report_date),
                "reports_created": 0,
                "message": "Нет заказов за указанную дату"
            }

        report_repo = ReportRepository()

        # Удаляем старые отчеты за эту дату (если есть)
        deleted_count = await report_repo.delete_by_date(session, report_date)
        if deleted_count > 0:
            print(f"[TaskIQ] Удалено старых отчетов: {deleted_count}")

        # Создаем отчет для каждого заказа
        reports_created = 0
        for order in orders:
            # Подсчитываем количество продуктов в заказе
            items_result = await session.execute(
                select(func.sum(OrderItem.quantity))
                .where(OrderItem.order_id == order.id)
            )
            total_products = items_result.scalar() or 0

            # Создаем запись в отчете только если есть продукты
            if total_products > 0:
                report_data = ReportCreate(
                    report_at=report_date,
                    order_id=order.id,
                    count_product=total_products
                )
                await report_repo.create(session, report_data)
                reports_created += 1

        print(f"[TaskIQ] Отчет за {report_date} сформирован. Создано записей: {reports_created}")

        return {
            "status": "success",
            "date": str(report_date),
            "reports_created": reports_created,
            "orders_processed": len(orders)
        }
