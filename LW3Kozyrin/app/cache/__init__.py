"""Модуль для работы с кэшированием"""
from app.cache.redis_client import redis_client, RedisClient

__all__ = ["redis_client", "RedisClient"]
