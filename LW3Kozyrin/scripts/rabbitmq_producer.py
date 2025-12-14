"""
Продюсер данных для RabbitMQ
Создает тестовые продукты и заказы для проверки работы приложения
"""
import asyncio
import aio_pika
import json
import os


async def send_message(channel, queue_name: str, message: dict):
    """Отправка сообщения в очередь"""
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key=queue_name
    )
    print(f"✓ Отправлено в '{queue_name}': {message}")


async def main():
    """Основная функция для отправки тестовых данных"""

    # Подключение к RabbitMQ
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/local")

    print("Подключение к RabbitMQ...")
    connection = await aio_pika.connect_robust(rabbitmq_url)

    async with connection:
        channel = await connection.channel()

        # Объявляем очереди
        await channel.declare_queue("product", durable=True)
        await channel.declare_queue("order", durable=True)

        print("\n=== Создание 5 продуктов ===\n")

        # Создание 5 продуктов
        products = [
            {
                "action": "create",
                "name": "Ноутбук ASUS ROG",
                "price": 95000.0,
                "stock_quantity": 15
            },
            {
                "action": "create",
                "name": "Смартфон iPhone 14",
                "price": 85000.0,
                "stock_quantity": 20
            },
            {
                "action": "create",
                "name": "Наушники Sony WH-1000XM5",
                "price": 25000.0,
                "stock_quantity": 30
            },
            {
                "action": "create",
                "name": "Клавиатура Logitech MX Keys",
                "price": 12000.0,
                "stock_quantity": 50
            },
            {
                "action": "create",
                "name": "Мышь Logitech MX Master 3",
                "price": 8500.0,
                "stock_quantity": 40
            }
        ]

        for product in products:
            await send_message(channel, "product", product)
            await asyncio.sleep(0.5)  # Небольшая задержка между сообщениями

        print("\n=== Ожидание обработки продуктов (3 секунды) ===\n")
        await asyncio.sleep(3)

        print("\n=== Создание 3 заказов ===\n")

        # Создание 3 заказов
        orders = [
            {
                "action": "create",
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 1, "quantity": 1},
                    {"product_id": 3, "quantity": 2}
                ]
            },
            {
                "action": "create",
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 2, "quantity": 1},
                    {"product_id": 4, "quantity": 1},
                    {"product_id": 5, "quantity": 1}
                ]
            },
            {
                "action": "create",
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 1, "quantity": 2}
                ]
            }
        ]

        for order in orders:
            await send_message(channel, "order", order)
            await asyncio.sleep(0.5)

        print("\n=== Обновление статуса заказа ===\n")
        await asyncio.sleep(2)

        # Обновление статуса заказа
        status_update = {
            "action": "update_status",
            "id": 1,
            "status": "processing"
        }
        await send_message(channel, "order", status_update)

        print("\n=== Пометка продукта как закончившегося ===\n")
        await asyncio.sleep(1)

        # Пометить продукт как закончившийся
        mark_out_of_stock = {
            "action": "mark_out_of_stock",
            "id": 3
        }
        await send_message(channel, "product", mark_out_of_stock)

        print("\n=== Попытка создать заказ с закончившимся товаром ===\n")
        await asyncio.sleep(1)

        # Попытка заказа с товаром, которого нет на складе (должна быть отклонена)
        failed_order = {
            "action": "create",
            "user_id": 1,
            "address_id": 1,
            "items": [
                {"product_id": 3, "quantity": 1}
            ]
        }
        await send_message(channel, "order", failed_order)

        print("\n✓ Все сообщения отправлены!")
        print("Проверьте логи брокера для подтверждения обработки")
        print("Откройте RabbitMQ UI: http://localhost:15672 (guest/guest)")


if __name__ == "__main__":
    asyncio.run(main())
