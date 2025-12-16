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
по лабораторной работе №6  
</p>

<p align="center">
<b>«Основы работы с RabbitMQ»</b>
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




## Цель работы

Освоить основные принципы работы с брокером сообщений RabbitMQ в Python, изучить различные паттерны обмена сообщений и научиться создавать распределенные приложения.

## Описание задачи

На основе ЛР5 интегрировать RabbitMQ для обработки операций с продуктами и заказами через очереди сообщений. Реализовать:

1. Подключение RabbitMQ через Docker Compose
2. Создание брокера с FastStream для обработки сообщений
3. Обработку операций создания, обновления продуктов и заказов
4. Проверку наличия товара на складе перед созданием заказа
5. REST API для получения информации о продуктах и заказах
6. Producer для отправки тестовых данных

## Ход выполнения

### 1. Настройка Docker Compose с RabbitMQ

В `docker-compose.yaml` добавлен сервис RabbitMQ с Management UI:

    rabbitmq:
      image: rabbitmq:3-management
      container_name: litestar_rabbitmq
      ports:
        - "5672:5672"   # AMQP порт
        - "15672:15672" # Management UI
      environment:
        - RABBITMQ_DEFAULT_USER=guest
        - RABBITMQ_DEFAULT_PASS=guest
        - RABBITMQ_DEFAULT_VHOST=local
      volumes:
        - rabbitmq_data:/var/lib/rabbitmq
      healthcheck:
        test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
        interval: 10s
        timeout: 5s
        retries: 5

**Пояснение:**
- Используется официальный образ `rabbitmq:3-management` с веб-интерфейсом
- Порт 5672 - для AMQP протокола (подключение приложений)
- Порт 15672 - для Management UI (мониторинг через браузер)
- Virtual host `local` для изоляции очередей
- Healthcheck для проверки готовности сервиса

### 2. Установка зависимостей

В `requirements.txt` добавлены:


    faststream[rabbit]>=0.5.0
    aio-pika>=9.0.0


**Пояснение:**
- `faststream[rabbit]` - высокоуровневый фреймворк для работы с RabbitMQ
- `aio-pika` - асинхронная библиотека для низкоуровневой работы с AMQP

### 3. Создание схем для сообщений

Файл `app/schemas/message_schema.py`:


    class ProductMessage(BaseModel):
        """Схема сообщения для создания/обновления продукта"""
        action: str  # create, update, mark_out_of_stock
        id: Optional[int]
        name: Optional[str]
        price: Optional[float]
        stock_quantity: Optional[int]
    
    class OrderMessage(BaseModel):
        """Схема сообщения для создания/обновления заказа"""
        action: str  # create, update_status
        id: Optional[int]
        user_id: Optional[int]
        address_id: Optional[int]
        items: Optional[List[OrderItemMessage]]
        status: Optional[OrderStatus]


**Пояснение:**
- Единые схемы для валидации сообщений из очередей
- Поле `action` определяет тип операции
- Опциональные поля для разных типов действий

### 4. Реализация RabbitMQ брокера

Файл `app/broker/rabbitmq_broker.py` содержит:

#### Подписчик на очередь "product":

    @broker.subscriber("product")
    async def subscribe_product(message: ProductMessage):
        """Обработчик сообщений для продуктов"""
        
        if message.action == "create":
            # Создание нового продукта
            product_data = ProductCreate(...)
            product = await product_repo.create(session, product_data)
            
        elif message.action == "update":
            # Обновление продукта
            update_data = ProductUpdate(...)
            product = await product_repo.update(session, message.id, update_data)
            
        elif message.action == "mark_out_of_stock":
            # Пометить продукт как закончившийся
            update_data = ProductUpdate(stock_quantity=0)
            await product_repo.update(session, message.id, update_data)

**Возможности:**
- Создание новых продуктов с заданием количества на складе
- Обновление информации о продукте (название, цена, количество)
- Пометка продукта как закончившегося (stock_quantity = 0)

#### Подписчик на очередь "order":

    @broker.subscriber("order")
    async def subscribe_order(message: OrderMessage):
        """Обработчик сообщений для заказов"""
        
        if message.action == "create":
            # Проверка наличия товаров на складе
            for item in message.items:
                product = await product_repo.get_by_id(session, item.product_id)
                
                if product.stock_quantity == 0:
                    logger.error(f"Продукт {product.name} закончился на складе")
                    return  # Заказ не создается
                
                if product.stock_quantity < item.quantity:
                    logger.error(f"Недостаточно товара на складе")
                    return  # Заказ не создается
            
            # Создание заказа
            order = await order_repo.create(session, order_data)
            
            # Уменьшение количества товара на складе
            for item in message.items:
                product = await product_repo.get_by_id(session, item.product_id)
                new_quantity = product.stock_quantity - item.quantity
                await product_repo.update(session, item.product_id, 
                                        ProductUpdate(stock_quantity=new_quantity))
        
        elif message.action == "update_status":
            # Обновление статуса заказа
            update_data = OrderUpdate(status=message.status)
            await order_repo.update(session, message.id, update_data)

**Ключевые особенности:**
- Проверка наличия товара **перед** созданием заказа
- Отклонение заказа, если товар закончился (stock_quantity = 0)
- Отклонение заказа при недостаточном количестве товара
- Автоматическое уменьшение остатков после успешного заказа
- Обновление статуса заказа (pending → processing → shipped → delivered)

### 5. REST API контроллеры

#### ProductController (`app/controllers/product_controller.py`):

    
    @get("/{product_id:int}")
    async def get_product(...) -> ProductResponse:
        """Получить продукт по ID"""
        
    @get("/")
    async def get_all_products(...) -> ProductListResponse:
        """Получить список всех продуктов с фильтрацией"""


#### OrderController (`app/controllers/order_controller.py`):


    @get("/{order_id:int}")
    async def get_order(...) -> OrderResponse:
        """Получить заказ по ID"""
        
    @get("/")
    async def get_all_orders(...) -> OrderListResponse:
        """Получить список всех заказов с фильтрацией"""
        
    @get("/user/{user_id:int}")
    async def get_user_orders(...) -> OrderListResponse:
        """Получить все заказы пользователя"""


**Пояснение:**
- REST API используется **только для чтения** (GET запросы)
- Операции создания/обновления выполняются через RabbitMQ
- Это обеспечивает асинхронную обработку и масштабируемость

### 6. Producer для тестирования

Скрипт `scripts/rabbitmq_producer.py` отправляет тестовые данные:

    # 5 продуктов
    products = [
        {"action": "create", "name": "Ноутбук ASUS ROG", 
         "price": 95000.0, "stock_quantity": 15},
        {"action": "create", "name": "Смартфон iPhone 14", 
         "price": 85000.0, "stock_quantity": 20},
        # ... еще 3 продукта
    ]
    
    # 3 заказа
    orders = [
        {"action": "create", "user_id": 1, "address_id": 1,
         "items": [{"product_id": 1, "quantity": 1}]},
        # ... еще 2 заказа
    ]
    
    # Обновление статуса
    {"action": "update_status", "id": 1, "status": "processing"}
    
    # Пометка как закончившегося
    {"action": "mark_out_of_stock", "id": 3}
    
    # Попытка заказа закончившегося товара (будет отклонена)
    {"action": "create", "items": [{"product_id": 3, "quantity": 1}]}
    
    
    **Демонстрация работы:**
    1. Создание 5 продуктов с разным количеством на складе
    2. Создание 3 заказов с автоматическим уменьшением остатков
    3. Обновление статуса заказа
    4. Пометка продукта как закончившегося
    5. Попытка заказа закончившегося товара (отклоняется)

### 7. Запуск и тестирование

**Запуск всей системы:**

    docker compose up --build

**Запуск брокера отдельно (в отдельном терминале):**

    docker compose exec app python -m app.broker.rabbitmq_broker

**Запуск producer для отправки тестовых данных:**

    docker compose exec app python scripts/rabbitmq_producer.py

    
<img width="1682" height="744" alt="Снимок экрана 2025-12-16 в 05 39 42" src="https://github.com/user-attachments/assets/09667557-ec10-4701-bbaa-e3ec9536eaf2" />


**Проверка через RabbitMQ UI:**
- Откройте http://localhost:15672
- Логин/пароль: guest/guest
- Вкладка "Queues" - проверка очередей и сообщений

**Проверка через REST API:**


    # Получить все продукты
    curl http://localhost:8000/products/
    
    # Получить продукт по ID
    curl http://localhost:8000/products/1
    
    # Получить все заказы
    curl http://localhost:8000/orders/
    
    # Получить заказы пользователя
    curl http://localhost:8000/orders/user/1


## Ответы на вопросы

### 1. Что такое AMQP? Каковы его основные преимущества?

**AMQP (Advanced Message Queuing Protocol)** - это открытый стандартный протокол прикладного уровня для передачи сообщений между приложениями через брокер сообщений.

**Основные преимущества AMQP:**

1. **Надежность доставки**
   - Гарантия доставки сообщений (at-least-once, at-most-once, exactly-once)
   - Подтверждение получения (acknowledgments)
   - Персистентность сообщений

2. **Гибкость маршрутизации**
   - Различные типы exchange (direct, topic, fanout, headers)
   - Сложные схемы маршрутизации через routing keys
   - Поддержка множественных очередей и binding'ов

3. **Платформонезависимость**
   - Работает на разных языках программирования
   - Единый стандарт взаимодействия
   - Совместимость разных реализаций (RabbitMQ, ActiveMQ, Qpid)

4. **Масштабируемость**
   - Распределение нагрузки между consumers
   - Кластеризация и репликация
   - Асинхронная обработка больших объемов данных

5. **Безопасность**
   - Аутентификация и авторизация
   - Шифрование соединений (TLS/SSL)
   - Изоляция через virtual hosts

### 2. В чем разница между очередями сообщений и шинами сообщений?

**Очередь сообщений (Message Queue):**

- **Модель:** Point-to-Point (один отправитель → один получатель)
- **Доставка:** Каждое сообщение обрабатывается только одним consumer
- **Порядок:** Сообщения обрабатываются в порядке поступления (FIFO)
- **Примеры:** RabbitMQ, Amazon SQS, Azure Queue Storage
- **Использование:** Обработка задач, распределение нагрузки, асинхронные операции


**Шина сообщений (Message Bus / Event Bus):**

- **Модель:** Publish-Subscribe (один отправитель → много получателей)
- **Доставка:** Каждое сообщение доставляется всем подписчикам
- **Порядок:** Может не сохраняться между разными подписчиками
- **Примеры:** Kafka, Redis Pub/Sub, Azure Service Bus
- **Использование:** Event-driven архитектура, уведомления, интеграция систем


**Ключевые различия:**

| Характеристика | Очередь сообщений | Шина сообщений |
|----------------|-------------------|----------------|
| Паттерн | Point-to-Point | Publish-Subscribe |
| Получатели | Один consumer | Все подписчики |
| Удаление | После обработки | Не удаляется или TTL |
| Балансировка | Автоматическая | Каждый обрабатывает |
| Использование | Задачи, обработка | События, уведомления |

**Примечание:** RabbitMQ поддерживает оба паттерна через разные типы exchange.

### 3. Как обеспечить надежную доставку сообщений в RabbitMQ?

**Механизмы обеспечения надежности:**

**1. Publisher Confirms (подтверждения от брокера)**

    # Включаем режим подтверждений
    channel.confirm_delivery()
    
    # Отправка с подтверждением
    try:
        channel.basic_publish(
            exchange='',
            routing_key='queue_name',
            body='message',
            properties=pika.BasicProperties(delivery_mode=2)  # Персистентность
        )
        print("Сообщение доставлено")
    except Exception:
        print("Ошибка доставки")

**2. Consumer Acknowledgments (подтверждения от получателя)**

    @broker.subscriber("queue_name", auto_ack=False)
    async def process_message(message):
        try:
            # Обработка сообщения
            await process(message)
            # Подтверждение успешной обработки
            await message.ack()
        except Exception:
            # Отклонение и возврат в очередь
            await message.nack(requeue=True)

**3. Персистентность сообщений**

    # Объявление durable очереди
    await channel.declare_queue("my_queue", durable=True)
    
    # Отправка персистентных сообщений
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=b"message",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT  # Сохранение на диск
        ),
        routing_key="my_queue"
    )

**4. Dead Letter Exchange (DLX)**

    # Очередь с DLX для необработанных сообщений
    await channel.declare_queue(
        "main_queue",
        durable=True,
        arguments={
            "x-dead-letter-exchange": "dlx_exchange",
            "x-message-ttl": 60000,  # TTL 60 секунд
            "x-max-retries": 3
        }
    )

**5. Transactions (транзакции)**

    # Начало транзакции
    await channel.tx_select()
    
    try:
        # Отправка нескольких сообщений
        await channel.basic_publish(...)
        await channel.basic_publish(...)
        
        # Коммит транзакции
        await channel.tx_commit()
    except Exception:
        # Откат транзакции
        await channel.tx_rollback()


**6. Prefetch Count (ограничение необработанных)**

    # Ограничиваем количество необработанных сообщений
    await channel.set_qos(prefetch_count=1)


**Рекомендуемая стратегия:**
- Publisher Confirms + Consumer Acknowledgments
- Персистентные очереди и сообщения
- Dead Letter Exchange для failed messages
- Prefetch count для контроля нагрузки

### 4. Что произойдет с сообщением, если consumer упадет во время обработки?

**Поведение зависит от режима acknowledgments:**

**Сценарий 1: Auto-Acknowledgment (auto_ack=True)**

    @broker.subscriber("queue", auto_ack=True)
    async def process(message):
        # Сообщение автоматически подтверждается при получении
        await long_operation()  # Consumer падает здесь
        # CООБЩЕНИЕ ПОТЕРЯНО

**Результат:** Сообщение удаляется из очереди сразу после отправки consumer'у, даже если обработка не завершилась. **Сообщение теряется!**

**Сценарий 2: Manual Acknowledgment (auto_ack=False) - РЕКОМЕНДУЕТСЯ**


    @broker.subscriber("queue", auto_ack=False)
    async def process(message):
        try:
            await long_operation()  # Consumer падает здесь
            await message.ack()  # Не выполнится
        except Exception:
            await message.nack(requeue=True)


**Результат:** RabbitMQ обнаруживает обрыв соединения и **автоматически возвращает сообщение в очередь** для повторной обработки другим consumer'ом.

**Детальный процесс:**

1. **Consumer получает сообщение** - RabbitMQ переводит его в статус "unacked"
2. **Consumer начинает обработку** - сообщение остается в unacked
3. **Consumer падает** - TCP соединение разрывается
4. **RabbitMQ обнаруживает разрыв** - через heartbeat или таймаут
5. **Сообщение возвращается в очередь** - автоматический requeue
6. **Другой consumer получает сообщение** - повторная попытка обработки

**Настройка heartbeat для быстрого обнаружения:**


    connection = await aio_pika.connect_robust(
        RABBITMQ_URL,
        heartbeat=30  # Проверка каждые 30 секунд
    )


**Защита от бесконечных повторов:**

    @broker.subscriber("queue", auto_ack=False)
    async def process(message):
        retry_count = message.headers.get("x-retry-count", 0)
        
        if retry_count > 3:
            # Отправляем в DLQ после 3 попыток
            await message.nack(requeue=False)
            return
        
        try:
            await long_operation()
            await message.ack()
        except Exception:
            # Увеличиваем счетчик попыток
            await message.nack(
                requeue=True,
                headers={"x-retry-count": retry_count + 1}
            )


### 5. Как обеспечить сохранность сообщений при перезапуске RabbitMQ?

**Требуется настроить персистентность на трех уровнях:**

**1. Durable Queues (персистентные очереди)**

**2. Persistent Messages (персистентные сообщения)**

**3. Durable Exchanges (персистентные exchange)**


**Важные моменты:**

**✓ Что сохраняется при перезапуске:**
- Durable очереди
- Durable exchanges
- Bindings между durable компонентами
- Persistent сообщения в durable очередях

**✗ Что НЕ сохраняется:**
- Non-durable (temporary) очереди
- Non-durable exchanges
- Transient сообщения (delivery_mode=1)
- Unacknowledged сообщения (возвращаются в очередь)


### 6. Что такое TTL (Time To Live) для сообщений и как его настроить?

**TTL (Time To Live)** - это время жизни сообщения, после которого оно автоматически удаляется из очереди или перемещается в Dead Letter Exchange.

**Применение TTL:**
- Автоматическое удаление устаревших сообщений
- Реализация таймаутов для задач
- Очистка очередей от необработанных данных
- Delayed/Scheduled сообщения

**Способы настройки TTL:**

**1. TTL для отдельного сообщения**
    
    import aio_pika
    
    # TTL в миллисекундах (60000 = 60 секунд)
    message = aio_pika.Message(
        body=b"temporary message",
        expiration="60000"  # Строка с TTL в мс
    )
    
    await channel.default_exchange.publish(
        message,
        routing_key="my_queue"
    )
    # Сообщение удалится через 60 секунд, если не обработано

**2. TTL для всей очереди (все сообщения)**


    # Все сообщения в очереди имеют TTL 30 секунд
    queue = await channel.declare_queue(
        "temp_queue",
        durable=True,
        arguments={
            "x-message-ttl": 30000  # 30 секунд в миллисекундах
        }
    )


**3. TTL для самой очереди (автоудаление)**

    # Очередь удалится через 1 час, если не используется
    queue = await channel.declare_queue(
        "auto_delete_queue",
        arguments={
            "x-expires": 3600000  # 1 час в миллисекундах
        }
    )


**4. TTL с Dead Letter Exchange**

    # Создаем DLX для expired сообщений
    dlx = await channel.declare_exchange(
        "expired_exchange",
        type="fanout",
        durable=True
    )
    
    dlq = await channel.declare_queue(
        "expired_queue",
        durable=True
    )
    await dlq.bind(dlx)
    
    # Основная очередь с TTL и DLX
    main_queue = await channel.declare_queue(
        "main_queue",
        durable=True,
        arguments={
            "x-message-ttl": 60000,  # TTL 60 секунд
            "x-dead-letter-exchange": "expired_exchange"  # Куда отправлять expired
        }
    )
    
    # Сообщения, не обработанные за 60 сек, попадут в expired_queue


**5. Delayed/Scheduled сообщения (паттерн)**

    
    # Создаем delay очередь без consumers
    delay_queue = await channel.declare_queue(
        "delay_30s",
        durable=True,
        arguments={
            "x-message-ttl": 30000,  # Задержка 30 секунд
            "x-dead-letter-exchange": "main_exchange",
            "x-dead-letter-routing-key": "process"
        }
    )
    
    # Отправка в delay очередь
    await channel.default_exchange.publish(
        aio_pika.Message(body=b"delayed message"),
        routing_key="delay_30s"
    )
    # Через 30 секунд сообщение попадет в main_exchange → process


**Практический пример - система уведомлений:**


    async def setup_notification_system():
        connection = await aio_pika.connect_robust("amqp://localhost/")
        channel = await connection.channel()
        
        # DLX для истекших уведомлений
        expired_exchange = await channel.declare_exchange(
            "expired_notifications",
            type="fanout",
            durable=True
        )
        
        # Очередь для логирования истекших
        expired_queue = await channel.declare_queue(
            "expired_logs",
            durable=True
        )
        await expired_queue.bind(expired_exchange)
        
        # Основная очередь уведомлений с TTL
        notifications_queue = await channel.declare_queue(
            "notifications",
            durable=True,
            arguments={
                "x-message-ttl": 300000,  # 5 минут
                "x-dead-letter-exchange": "expired_notifications"
            }
        )
        
        # Отправка уведомления с индивидуальным TTL
        urgent_notification = aio_pika.Message(
            body=b"Urgent: Server is down!",
            expiration="10000",  # Срочное - 10 секунд
            priority=10
        )
        
        normal_notification = aio_pika.Message(
            body=b"Daily report ready",
            expiration="300000",  # Обычное - 5 минут
            priority=1
        )
        
        await channel.default_exchange.publish(
            urgent_notification,
            routing_key="notifications"
        )


**Важные моменты:**

1. **TTL начинает отсчет с момента попадания в очередь**, а не с момента отправки
2. **Expired сообщения удаляются только с головы очереди** (если не используется DLX)
3. **Индивидуальный TTL имеет приоритет** над TTL очереди
4. **TTL = 0 означает немедленное истечение** (полезно для DLX паттернов)
5. **С DLX можно реализовать retry logic** с нарастающими задержками


## Выводы

В ходе выполнения лабораторной работы были освоены основные принципы работы с брокером сообщений RabbitMQ. Создано распределенное приложение с асинхронной обработкой операций через очереди сообщений.

**Основные достижения:**

1. **Интеграция RabbitMQ** - настроен Docker Compose с RabbitMQ Management, установлены необходимые библиотеки (faststream, aio-pika).

2. **Реализован брокер сообщений** - создан FastStream брокер с подписчиками на очереди "product" и "order", реализована обработка различных действий (create, update, mark_out_of_stock, update_status).

3. **Бизнес-логика** - реализована проверка наличия товара на складе перед созданием заказа, автоматическое уменьшение остатков, отклонение заказов с закончившимися товарами.

4. **REST API** - созданы контроллеры для получения информации о продуктах и заказах через HTTP, разделение ответственности: запись через RabbitMQ, чтение через REST API.

5. **Тестирование** - создан producer для автоматической отправки тестовых данных, демонстрация всех возможностей системы.


</div>
