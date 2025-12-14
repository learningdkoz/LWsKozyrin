"""Клиент для работы с Redis"""
import json
import os
from typing import Optional, Any
import redis.asyncio as redis
from redis.asyncio import Redis


class RedisClient:
    """Класс для работы с Redis кэшем"""

    def __init__(self):
        """Инициализация клиента Redis"""
        self._redis: Optional[Redis] = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    async def connect(self) -> None:
        """Подключение к Redis"""
        if self._redis is None:
            self._redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True  # Автоматическая декодировка ответов в строки
            )

    async def disconnect(self) -> None:
        """Отключение от Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def get(self, key: str) -> Optional[str]:
        """
        Получить значение по ключу

        Args:
            key: Ключ в Redis

        Returns:
            Значение или None, если ключ не найден
        """
        if not self._redis:
            await self.connect()
        return await self._redis.get(key)

    async def set(
            self,
            key: str,
            value: Any,
            expire: Optional[int] = None
    ) -> bool:
        """
        Установить значение по ключу с опциональным TTL

        Args:
            key: Ключ в Redis
            value: Значение для сохранения
            expire: Время жизни ключа в секундах (TTL)

        Returns:
            True если успешно установлено
        """
        if not self._redis:
            await self.connect()

        # Если значение - словарь или объект, сериализуем в JSON
        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        return await self._redis.set(key, value, ex=expire)

    async def delete(self, key: str) -> int:
        """
        Удалить ключ из Redis

        Args:
            key: Ключ для удаления

        Returns:
            Количество удаленных ключей (0 или 1)
        """
        if not self._redis:
            await self.connect()
        return await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """
        Проверить существование ключа

        Args:
            key: Ключ для проверки

        Returns:
            True если ключ существует
        """
        if not self._redis:
            await self.connect()
        return await self._redis.exists(key) > 0

    async def get_ttl(self, key: str) -> int:
        """
        Получить оставшееся время жизни ключа

        Args:
            key: Ключ для проверки

        Returns:
            Оставшееся время в секундах, -1 если ключ без TTL, -2 если ключа не существует
        """
        if not self._redis:
            await self.connect()
        return await self._redis.ttl(key)

    async def set_json(
            self,
            key: str,
            value: dict,
            expire: Optional[int] = None
    ) -> bool:
        """
        Сохранить JSON объект в Redis

        Args:
            key: Ключ в Redis
            value: Словарь для сохранения
            expire: Время жизни в секундах

        Returns:
            True если успешно
        """
        json_value = json.dumps(value)
        return await self.set(key, json_value, expire)

    async def get_json(self, key: str) -> Optional[dict]:
        """
        Получить JSON объект из Redis

        Args:
            key: Ключ в Redis

        Returns:
            Словарь или None
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None


# Глобальный экземпляр клиента Redis
redis_client = RedisClient()
