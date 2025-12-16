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
по лабораторной работе №7  
</p>

<p align="center">
<b>«Основы работы с Redis»</b>
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
## Цель работы

Овладеть базовыми навыками установки, подключения и взаимодействия с Redis в Python. Изучить основные структуры данных Redis и их применение на практике.

## Описание задачи

В данной лабораторной работе выполнены следующие задачи:

1. Добавление контейнера Redis в Docker Compose
2. Создание клиента для работы с Redis
3. Изучение основных структур данных Redis (строки, списки, множества, хэши, упорядоченные множества)
4. Реализация кэширования данных пользователей (TTL 1 час) и продуктов (TTL 10 минут)
5. Реализация инвалидации кэша при обновлении данных

## Выполнение работы

### 1. Добавление контейнера Redis

В файл `docker-compose.yaml` добавлен сервис Redis:

```yaml
redis:
  image: redis:7-alpine
  container_name: litestar_redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - litestar_network
  restart: unless-stopped
```

**Описание конфигурации:**
- Используется официальный образ `redis:7-alpine`
- Порт 6379 проброшен на хост для локального доступа
- Данные сохраняются в volume `redis_data` для персистентности
- Healthcheck использует команду `redis-cli ping` для проверки работоспособности
- Сервис перезапускается автоматически при сбоях

### 2. Создание клиента Redis

Создан модуль `app/cache/redis_client.py` с классом `RedisClient`:

```python
class RedisClient:
    """Класс для работы с Redis кэшем"""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    async def connect(self) -> None:
        """Подключение к Redis с decode_responses=True"""
        if self._redis is None:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
```

**Ключевые особенности:**
- Асинхронное подключение через `redis.asyncio`
- Параметр `decode_responses=True` для автоматической декодировки байтов в строки
- Методы для работы с различными типами данных
- Поддержка TTL (Time To Live) для автоматического удаления ключей

### 3. Работа со структурами данных Redis

Создан демонстрационный скрипт `scripts/redis_demo.py`, который показывает работу со всеми основными структурами данных:

#### Строки (Strings)

```python
await r.set("name", "Дмитрий")
name = await r.get("name")
await r.set("temp_key", "temporary", ex=10)  # TTL 10 секунд
await r.incr("counter")  # Атомарный инкремент
```

#### Списки (Lists)

```python
await r.lpush("queue", "первый")  # Добавление в начало
await r.rpush("queue", "последний")  # Добавление в конец
items = await r.lrange("queue", 0, -1)  # Получение всех элементов
await r.lpop("queue")  # Извлечение из начала
```

**Разница между lpush и rpush:**
- `lpush()` - добавляет элемент в начало списка (left push)
- `rpush()` - добавляет элемент в конец списка (right push)
- При использовании `lpush` последний добавленный элемент будет первым
- При использовании `rpush` последний добавленный элемент будет последним

#### Множества (Sets)
```python
await r.sadd("tags", "python", "redis", "backend")
tags = await r.smembers("tags")  # Получение всех элементов
exists = await r.sismember("tags", "python")  # Проверка наличия
intersection = await r.sinter("tags", "skills")  # Пересечение множеств
```

#### Хэши (Hashes)
```python
await r.hset("user:1000", mapping={
    "username": "dmitry",
    "email": "dmitry@example.com"
})
username = await r.hget("user:1000", "username")
user = await r.hgetall("user:1000")
```

#### Упорядоченные множества (Sorted Sets)
```python
await r.zadd("leaderboard", {"Alice": 100, "Bob": 150})
top = await r.zrevrange("leaderboard", 0, 2, withscores=True)
await r.zincrby("leaderboard", 30, "Alice")
```

### 4. Реализация кэширования

#### Кэширование пользователей (TTL 1 час)

В `app/repositories/user_repository.py`:

```python
async def get_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
    # Проверка кэша
    cache_key = f"user:{user_id}"
    cached_data = await redis_client.get_json(cache_key)
    
    if cached_data:
        return User(**cached_data)
    
    # Запрос к БД если нет в кэше
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user:
        # Сохранение в кэш на 1 час (3600 секунд)
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name
        }
        await redis_client.set_json(cache_key, user_dict, expire=3600)
    
    return user
```

**Инвалидация кэша при обновлении:**
```python
async def update(self, session: AsyncSession, user_id: int, user_data: UserUpdate):
    # ... обновление в БД ...
    
    # Удаление из кэша после обновления
    cache_key = f"user:{user_id}"
    await redis_client.delete(cache_key)
    
    return user
```

#### Кэширование продуктов (TTL 10 минут)

В `app/repositories/product_repository.py`:

```python
async def get_by_id(self, session: AsyncSession, product_id: int) -> Optional[Product]:
    cache_key = f"product:{product_id}"
    cached_data = await redis_client.get_json(cache_key)
    
    if cached_data:
        return Product(**cached_data)
    
    # ... запрос к БД ...
    
    if product:
        # Сохранение в кэш на 10 минут (600 секунд)
        await redis_client.set_json(cache_key, product_dict, expire=600)
    
    return product
```

**Обновление кэша при изменении данных:**
```python
async def update(self, session: AsyncSession, product_id: int, product_data: ProductUpdate):
    # ... обновление в БД ...
    
    # Обновление данных в кэше (не удаление)
    cache_key = f"product:{product_id}"
    product_dict = {
        "id": product.id,
        "name": product.name,
        "price": float(product.price),
        "stock_quantity": product.stock_quantity
    }
    await redis_client.set_json(cache_key, product_dict, expire=600)
    
    return product
```

### 5. Интеграция с Litestar

В `app/main.py` добавлены хуки для управления жизненным циклом Redis:

```python
async def init_redis() -> None:
    """Инициализация Redis при запуске приложения"""
    await redis_client.connect()

async def close_redis() -> None:
    """Закрытие подключения к Redis при остановке приложения"""
    await redis_client.disconnect()

app = Litestar(
    # ...
    on_startup=[init_database, init_redis],
    on_shutdown=[close_redis],
)
```

## Запуск проекта

### Запуск через Docker Compose

```bash
# Запуск всех сервисов
docker compose up --build

# Проверка работы Redis
docker exec -it litestar_redis redis-cli ping
# Ответ: PONG

# Просмотр логов Redis
docker compose logs redis
```

<img width="845" height="110" alt="Снимок экрана 2025-12-16 в 12 33 45" src="https://github.com/user-attachments/assets/6bb0ef66-3ef6-4676-beab-495c2a1a0e82" />

<img width="743" height="105" alt="Снимок экрана 2025-12-16 в 12 34 36" src="https://github.com/user-attachments/assets/566ce977-066a-4d3c-8dd6-6f54a8c56e68" />

### Запуск демонстрационного скрипта

```bash
# Внутри контейнера
docker exec -it litestar_app python scripts/redis_demo.py

# Или локально (если Redis запущен)
python scripts/redis_demo.py
```

<img width="1138" height="549" alt="Снимок экрана 2025-12-16 в 12 45 59" src="https://github.com/user-attachments/assets/1e3aaf4d-0c4e-45b0-8587-5aad75ff3885" />

### Тестирование кэширования через API

```bash
# Создание пользователя
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "full_name": "Test User"}'

# Первый запрос - данные из БД, сохранение в кэш
curl http://localhost:8000/users/1

# Второй запрос - данные из кэша (быстрее)
curl http://localhost:8000/users/1

# Обновление пользователя - кэш инвалидируется
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Updated User"}'

# Следующий запрос снова идет в БД
curl http://localhost:8000/users/1
```

### Мониторинг Redis


```bash
# Подключение к Redis CLI
docker exec -it litestar_redis redis-cli

# Просмотр всех ключей
KEYS *

# Получение информации о ключе
TTL user:1

# Просмотр значения
GET user:1

# Статистика Redis
INFO stats
```

## Ответы на вопросы

### 1. В чем заключается основное преимущество хранения данных в оперативной памяти (in-memory) по сравнению с дисковыми БД?

**Основные преимущества:**

1. **Скорость доступа**: Оперативная память (RAM) обеспечивает время доступа в микросекундах, в то время как дисковые БД имеют латентность в миллисекундах. Это разница в тысячи раз.

2. **Пропускная способность**: Redis может выполнять сотни тысяч операций в секунду на одном сервере, что недостижимо для дисковых БД.

3. **Простота архитектуры**: Отсутствие необходимости в сложных механизмах буферизации, индексации и управления страницами памяти упрощает архитектуру и повышает производительность.

4. **Предсказуемость**: Операции в памяти имеют стабильное и предсказуемое время выполнения, в отличие от дисковых операций, которые зависят от физических характеристик носителя.

5. **Низкая латентность**: Идеально для кэширования, сессий, реал-тайм аналитики и других задач, требующих минимальной задержки.

**Недостатки:**
- Ограниченный объем (RAM дороже диска)
- Риск потери данных при перезагрузке (решается через RDB/AOF персистентность)
- Высокая стоимость масштабирования

### 2. Для чего нужен параметр decode_responses=True при создании клиента Redis?

**Назначение параметра:**

По умолчанию Redis возвращает все значения в виде байтов (`bytes`). Параметр `decode_responses=True` автоматически декодирует эти байты в строки (strings) с использованием указанной кодировки.

**Преимущества:**
- Удобство работы со строковыми данными
- Отсутствие необходимости в ручной декодировке
- Более читаемый код
- Автоматическая обработка JSON и других текстовых форматов

**Когда НЕ использовать:**
- При работе с бинарными данными (изображения, файлы)
- Когда нужен полный контроль над кодировкой

### 3. Что такое TTL (Time To Live) ключа и как он используется в Redis?

**Определение:**

TTL (Time To Live) - это время жизни ключа в Redis, после истечения которого ключ автоматически удаляется. Измеряется в секундах.

**Преимущества TTL:**
- Автоматическая очистка устаревших данных
- Экономия памяти
- Не требует ручного управления жизненным циклом
- Предотвращает переполнение кэша

### 4. Объясните разницу между командами r.lpush() и r.rpush() для списков.

**Структура списка в Redis:**

Список в Redis - это двусторонняя очередь (deque), где можно добавлять и удалять элементы с обоих концов.

**r.lpush() - Left Push (добавление в начало):**

```python
await r.delete("queue")
await r.lpush("queue", "A")  # queue: [A]
await r.lpush("queue", "B")  # queue: [B, A]
await r.lpush("queue", "C")  # queue: [C, B, A]
result = await r.lrange("queue", 0, -1)
print(result)  # ['C', 'B', 'A']
```

**r.rpush() - Right Push (добавление в конец):**

```python
await r.delete("queue")
await r.rpush("queue", "A")  # queue: [A]
await r.rpush("queue", "B")  # queue: [A, B]
await r.rpush("queue", "C")  # queue: [A, B, C]
result = await r.lrange("queue", 0, -1)
print(result)  # ['A', 'B', 'C']
```

**Операции извлечения:**
- `lpop()` - извлечение из начала (HEAD)
- `rpop()` - извлечение из конца (TAIL)
- `blpop()` / `brpop()` - блокирующие версии для реализации очередей задач

### 5. Как обеспечить атомарность операций в Redis?

Redis обеспечивает атомарность операций на нескольких уровнях:

#### 1. Атомарность отдельных команд

Все команды Redis выполняются атомарно. Redis однопоточный (для обработки команд), поэтому каждая команда выполняется полностью до начала следующей.

```python
# Эти операции атомарны по умолчанию
await r.incr("counter")  # Атомарный инкремент
await r.lpush("list", "value")  # Атомарное добавление
await r.sadd("set", "member")  # Атомарное добавление в множество
```

#### 2. Транзакции (MULTI/EXEC)

Группировка нескольких команд в одну атомарную операцию:

```python
# Начало транзакции
pipe = r.pipeline()
pipe.multi()

# Добавление команд в транзакцию
pipe.incr("counter")
pipe.set("key1", "value1")
pipe.lpush("list", "item")

# Выполнение всех команд атомарно
results = await pipe.execute()
```

**Важно:** Транзакции Redis не поддерживают откат (rollback). Если команда в транзакции завершается с ошибкой, остальные команды все равно выполнятся.

#### 3. Lua скрипты

Наиболее мощный способ обеспечения атомарности - выполнение Lua скриптов на сервере:

```python
# Lua скрипт для атомарного инкремента с лимитом
lua_script = """
local current = redis.call('GET', KEYS[1])
if not current then
    current = 0
else
    current = tonumber(current)
end

if current < tonumber(ARGV[1]) then
    return redis.call('INCR', KEYS[1])
else
    return nil
end
```

**В нашем проекте атомарность обеспечивается:**
- Использованием встроенных атомарных команд Redis
- Простыми операциями set/get с TTL
- Каждая операция кэширования независима и атомарна

### 6. Как в Redis реализована репликация и кластеризация?

#### Репликация (Master-Slave / Master-Replica)

**Архитектура:**

```
        [Master]
       /    |    \
   [Replica1] [Replica2] [Replica3]
```

**Как работает:**

1. **Асинхронная репликация:**
   - Master принимает все записи
   - Изменения асинхронно реплицируются на Slave-серверы
   - Replica могут обслуживать запросы на чтение

2. **Настройка репликации:**

```bash
# На Replica сервере
redis-cli> REPLICAOF <master-ip> <master-port>

# Или в конфигурации redis.conf
replicaof 192.168.1.100 6379
```

**В Docker Compose:**

```yaml
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server
    ports:
      - "6379:6379"

  redis-replica-1:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379
    depends_on:
      - redis-master

  redis-replica-2:
    image: redis:7-alpine
    command: redis-server --replicaof redis-master 6379
    depends_on:
      - redis-master
```

**Преимущества репликации:**
- Высокая доступность (failover)
- Горизонтальное масштабирование чтения
- Резервное копирование данных
- Географическое распределение

**Ключевые особенности:**

1. **Шардирование данных:**
   - Данные автоматически распределяются по узлам
   - Используется хеш-слотирование (16384 слота)
   - Ключ определяет слот: `HASH_SLOT = CRC16(key) mod 16384`

2. **Автоматический failover:**
   - При падении Master, Replica автоматически становится Master
   - Кворум узлов принимает решение о failover

3. **Горизонтальное масштабирование:**
   - Добавление/удаление узлов без остановки
   - Автоматическая миграция слотов

**Настройка кластера в Docker:**

```yaml
services:
  redis-node-1:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
    ports:
      - "6379:6379"
      - "16379:16379"

  redis-node-2:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
    ports:
      - "6380:6379"
      - "16380:16379"

  redis-node-3:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf
    ports:
      - "6381:6379"
      - "16381:16379"
```

**Ограничения кластера:**
- Не поддерживаются операции с несколькими ключами из разных слотов
- Использование hash tags для группировки ключей: `{user:1000}:profile`, `{user:1000}:settings`

#### Сравнение подходов:

| Характеристика | Репликация | Кластеризация |
|----------------|------------|---------------|
| Масштабирование | Только чтение | Чтение и запись |
| Автоматический failover | Требует Sentinel | Встроен |
| Шардирование | Нет | Да |
| Сложность настройки | Простая | Средняя |
| Операции с несколькими ключами | Да | Ограничено |
| Подходит для | < 10GB данных | > 10GB данных |

**В нашем проекте:**

Используется простая single-node конфигурация Redis, достаточная для разработки и небольших проектов. Для production рекомендуется:
- Репликация для высокой доступности
- Redis Sentinel для автоматического failover
- Redis Cluster для больших объемов данных

## Выводы

В ходе выполнения лабораторной работы №7 были получены следующие результаты:

1. **Успешно интегрирован Redis** в существующую архитектуру приложения с использованием Docker Compose
2. **Реализован асинхронный клиент** для работы с Redis, поддерживающий все основные структуры данных
3. **Изучены и продемонстрированы** все типы данных Redis: строки, списки, множества, хэши и упорядоченные множества
4. **Внедрено кэширование** для критичных данных:
   - Пользователи: TTL 1 час, инвалидация при обновлении
   - Продукты: TTL 10 минут, обновление кэша при изменении
5. **Достигнуто ускорение** операций чтения за счет использования кэша в оперативной памяти
6. **Получены практические навыки** работы с Redis, включая управление TTL, атомарные операции и стратегии кэширования


