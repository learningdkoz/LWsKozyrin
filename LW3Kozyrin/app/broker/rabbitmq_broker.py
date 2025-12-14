"""RabbitMQ брокер с обработчиками сообщений"""
import os
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.schemas.message_schema import ProductMessage, OrderMessage
from app.repositories.product_repository import ProductRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.schemas.order_schema import OrderCreate, OrderItemCreate, OrderUpdate
from app.models.order import OrderStatus
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL подключения к RabbitMQ
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/local")

# URL подключения к БД
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/litestar_db"
)

# Создание брокера
broker = RabbitBroker(RABBITMQ_URL)
app = FastStream(broker)

# Создание движка БД для брокера
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Репозитории
product_repo = ProductRepository()
order_repo = OrderRepository()


async def get_db_session():
    """Получить сессию БД"""
    async with async_session_factory() as session:
        return session


@broker.subscriber("product")
async def subscribe_product(message: ProductMessage):
    """
    Обработчик сообщений для продуктов

    Поддерживаемые действия:
    - create: создание нового продукта
    - update: обновление существующего продукта
    - mark_out_of_stock: пометить продукт как закончившийся
    """
    logger.info(f"Получено сообщение для продукта: {message.action}")

    session = await get_db_session()

    try:
        if message.action == "create":
            # Создание нового продукта
            if not message.name or message.price is None or message.stock_quantity is None:
                logger.error("Недостаточно данных для создания продукта")
                return

            product_data = ProductCreate(
                name=message.name,
                price=message.price,
                stock_quantity=message.stock_quantity
            )
            product = await product_repo.create(session, product_data)
            logger.info(f"Создан продукт: {product.id} - {product.name}")

        elif message.action == "update":
            # Обновление продукта
            if not message.id:
                logger.error("Не указан ID продукта для обновления")
                return

            update_data = ProductUpdate(
                name=message.name,
                price=message.price,
                stock_quantity=message.stock_quantity
            )
            product = await product_repo.update(session, message.id, update_data)
            if product:
                logger.info(f"Обновлен продукт: {product.id}")
            else:
                logger.warning(f"Продукт {message.id} не найден")

        elif message.action == "mark_out_of_stock":
            # Пометить продукт как закончившийся (stock_quantity = 0)
            if not message.id:
                logger.error("Не указан ID продукта")
                return

            update_data = ProductUpdate(stock_quantity=0)
            product = await product_repo.update(session, message.id, update_data)
            if product:
                logger.info(f"Продукт {product.id} помечен как закончившийся")
            else:
                logger.warning(f"Продукт {message.id} не найден")
        else:
            logger.warning(f"Неизвестное действие: {message.action}")

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения продукта: {e}")
        await session.rollback()
    finally:
        await session.close()


@broker.subscriber("order")
async def subscribe_order(message: OrderMessage):
    """
    Обработчик сообщений для заказов

    Поддерживаемые действия:
    - create: создание нового заказа (проверяет наличие товара на складе)
    - update_status: обновление статуса заказа
    """
    logger.info(f"Получено сообщение для заказа: {message.action}")

    session = await get_db_session()

    try:
        if message.action == "create":
            # Создание нового заказа
            if not message.user_id or not message.address_id or not message.items:
                logger.error("Недостаточно данных для создания заказа")
                return

            # Проверка наличия товаров на складе
            for item in message.items:
                product = await product_repo.get_by_id(session, item.product_id)
                if not product:
                    logger.error(f"Продукт {item.product_id} не найден")
                    return

                if product.stock_quantity == 0:
                    logger.error(
                        f"Продукт {product.name} (ID: {item.product_id}) "
                        f"закончился на складе. Заказ не может быть создан."
                    )
                    return

                if product.stock_quantity < item.quantity:
                    logger.error(
                        f"Недостаточно товара {product.name} на складе. "
                        f"Запрошено: {item.quantity}, доступно: {product.stock_quantity}"
                    )
                    return

            # Создание заказа
            order_items = [
                OrderItemCreate(product_id=item.product_id, quantity=item.quantity)
                for item in message.items
            ]
            order_data = OrderCreate(
                user_id=message.user_id,
                address_id=message.address_id,
                items=order_items
            )
            order = await order_repo.create(session, order_data)
            logger.info(f"Создан заказ: {order.id} на сумму {order.total_price}")

            # Уменьшаем количество товара на складе
            for item in message.items:
                product = await product_repo.get_by_id(session, item.product_id)
                new_quantity = product.stock_quantity - item.quantity
                update_data = ProductUpdate(stock_quantity=new_quantity)
                await product_repo.update(session, item.product_id, update_data)
                logger.info(
                    f"Обновлен остаток товара {product.name}: "
                    f"{product.stock_quantity} -> {new_quantity}"
                )

        elif message.action == "update_status":
            # Обновление статуса заказа
            if not message.id or not message.status:
                logger.error("Не указан ID заказа или новый статус")
                return

            update_data = OrderUpdate(status=message.status)
            order = await order_repo.update(session, message.id, update_data)
            if order:
                logger.info(f"Обновлен статус заказа {order.id}: {order.status}")
            else:
                logger.warning(f"Заказ {message.id} не найден")
        else:
            logger.warning(f"Неизвестное действие: {message.action}")

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения заказа: {e}")
        await session.rollback()
    finally:
        await session.close()


@app.on_startup
async def on_startup():
    """Инициализация при запуске"""
    logger.info("Брокер RabbitMQ запущен и слушает очереди 'product' и 'order'")
