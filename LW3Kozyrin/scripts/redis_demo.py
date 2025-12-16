"""Демонстрационный скрипт для работы с Redis"""
import asyncio
import redis.asyncio as redis
import os


async def demo_strings(r: redis.Redis):
    """Демонстрация работы со строками"""
    print("\n=== Работа со строками ===")

    # SET и GET
    await r.set("name", "Дмитрий")
    name = await r.get("name")
    print(f"GET name: {name}")

    # SET с TTL
    await r.set("temp_key", "temporary", ex=10)
    ttl = await r.ttl("temp_key")
    print(f"TTL temp_key: {ttl} секунд")

    # INCR для счетчиков
    await r.set("counter", 0)
    await r.incr("counter")
    await r.incr("counter")
    counter = await r.get("counter")
    print(f"Counter после INCR: {counter}")


async def demo_lists(r: redis.Redis):
    """Демонстрация работы со списками"""
    print("\n=== Работа со списками ===")

    # LPUSH - добавление в начало списка
    await r.delete("queue")  # Очищаем список
    await r.lpush("queue", "первый")
    await r.lpush("queue", "второй")
    await r.lpush("queue", "третий")

    # RPUSH - добавление в конец списка
    await r.rpush("queue", "последний")

    # LRANGE - получение элементов списка
    items = await r.lrange("queue", 0, -1)
    print(f"Список queue: {items}")

    # LPOP - извлечение из начала
    first = await r.lpop("queue")
    print(f"LPOP извлек: {first}")

    # RPOP - извлечение с конца
    last = await r.rpop("queue")
    print(f"RPOP извлек: {last}")


async def demo_sets(r: redis.Redis):
    """Демонстрация работы с множествами"""
    print("\n=== Работа с множествами ===")

    # SADD - добавление элементов в множество
    await r.delete("tags")
    await r.sadd("tags", "python", "redis", "backend")
    await r.sadd("tags", "python")  # Дубликат не добавится

    # SMEMBERS - получение всех элементов
    tags = await r.smembers("tags")
    print(f"Множество tags: {tags}")

    # SISMEMBER - проверка наличия элемента
    exists = await r.sismember("tags", "python")
    print(f"'python' в tags: {exists}")

    # Операции над множествами
    await r.sadd("skills", "python", "docker", "git")
    intersection = await r.sinter("tags", "skills")
    print(f"Пересечение tags и skills: {intersection}")


async def demo_hashes(r: redis.Redis):
    """Демонстрация работы с хэшами"""
    print("\n=== Работа с хэшами ===")

    # HSET - установка полей хэша
    await r.hset("user:1000", mapping={
        "username": "dmitry",
        "email": "dmitry@example.com",
        "age": "25"
    })

    # HGET - получение одного поля
    username = await r.hget("user:1000", "username")
    print(f"Username: {username}")

    # HGETALL - получение всех полей
    user = await r.hgetall("user:1000")
    print(f"User 1000: {user}")

    # HINCRBY - инкремент числового поля
    await r.hincrby("user:1000", "age", 1)
    age = await r.hget("user:1000", "age")
    print(f"Age после инкремента: {age}")


async def demo_sorted_sets(r: redis.Redis):
    """Демонстрация работы с упорядоченными множествами"""
    print("\n=== Работа с упорядоченными множествами ===")

    # ZADD - добавление элементов с оценками
    await r.delete("leaderboard")
    await r.zadd("leaderboard", {
        "Alice": 100,
        "Bob": 150,
        "Charlie": 120,
        "David": 180
    })

    # ZRANGE - получение элементов по рангу (в порядке возрастания)
    top_asc = await r.zrange("leaderboard", 0, 2, withscores=True)
    print(f"Топ-3 (возрастание): {top_asc}")

    # ZREVRANGE - получение элементов в обратном порядке
    top_desc = await r.zrevrange("leaderboard", 0, 2, withscores=True)
    print(f"Топ-3 (убывание): {top_desc}")

    # ZINCRBY - инкремент оценки
    await r.zincrby("leaderboard", 30, "Alice")
    alice_score = await r.zscore("leaderboard", "Alice")
    print(f"Alice score после инкремента: {alice_score}")


async def demo_cache_operations(r: redis.Redis):
    """Демонстрация кэширования"""
    print("\n=== Кэширование запросов ===")

    # Кэширование данных пользователя на 1 час (3600 секунд)
    user_data = '{"id": 1, "username": "dmitry", "email": "dmitry@example.com"}'
    await r.set("cache:user:1", user_data, ex=3600)
    print("Данные пользователя закэшированы на 1 час")

    # Кэширование данных продукта на 10 минут (600 секунд)
    product_data = '{"id": 100, "name": "Laptop", "price": 1000}'
    await r.set("cache:product:100", product_data, ex=600)
    print("Данные продукта закэшированы на 10 минут")

    # Получение из кэша
    cached_user = await r.get("cache:user:1")
    print(f"Данные пользователя из кэша: {cached_user}")

    # Проверка TTL
    ttl = await r.ttl("cache:user:1")
    print(f"TTL кэша пользователя: {ttl} секунд")

    # Инвалидация кэша (удаление при обновлении)
    await r.delete("cache:user:1")
    print("Кэш пользователя удален после обновления")

    # Обновление кэша продукта
    updated_product = '{"id": 100, "name": "Laptop Pro", "price": 1200}'
    await r.set("cache:product:100", updated_product, ex=600)
    print("Кэш продукта обновлен")


async def main():
    """Главная функция для демонстрации работы с Redis"""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Подключение к Redis с decode_responses=True для автоматической декодировки
    r = await redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True
    )

    try:
        # Проверка подключения
        await r.ping()
        print("✓ Успешное подключение к Redis")

        # Запуск всех демонстраций
        await demo_strings(r)
        await demo_lists(r)
        await demo_sets(r)
        await demo_hashes(r)
        await demo_sorted_sets(r)
        await demo_cache_operations(r)

        print("\n=== Демонстрация завершена ===")

    finally:
        await r.close()


if __name__ == "__main__":
    asyncio.run(main())
