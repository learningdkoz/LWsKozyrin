import os
from litestar import Litestar
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.controllers.user_controller import UserController
from app.controllers.product_controller import ProductController
from app.controllers.order_controller import OrderController
from app.repositories.user_repository import UserRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.order_repository import OrderRepository
from app.services.user_service import UserService
from app.models.base import Base
from app.cache.redis_client import redis_client


# Настройка базы данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/litestar_db"
)

# Создание асинхронного движка
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# Создание фабрики сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def provide_db_session() -> AsyncSession:
    """Провайдер сессии базы данных"""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def provide_user_repository() -> UserRepository:
    """Провайдер репозитория пользователей"""
    return UserRepository()


def provide_product_repository() -> ProductRepository:
    """Провайдер репозитория продуктов"""
    return ProductRepository()


def provide_order_repository() -> OrderRepository:
    """Провайдер репозитория заказов"""
    return OrderRepository()


def provide_user_service(
    user_repository: UserRepository,
    db_session: AsyncSession
) -> UserService:
    """Провайдер сервиса пользователей"""
    return UserService(user_repository, db_session)


async def init_database() -> None:
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def init_redis() -> None:
    """Инициализация Redis при запуске приложения"""
    await redis_client.connect()
    print("✓ Redis успешно подключен")


async def close_redis() -> None:
    """Закрытие подключения к Redis при остановке приложения"""
    await redis_client.disconnect()
    print("✓ Redis отключен")


# Создание приложения Litestar
app = Litestar(
    route_handlers=[UserController, ProductController, OrderController],
    dependencies={
        "db_session": Provide(provide_db_session),
        "user_repository": Provide(provide_user_repository, sync_to_thread=False),
        "product_repository": Provide(provide_product_repository, sync_to_thread=False),
        "order_repository": Provide(provide_order_repository, sync_to_thread=False),
        "user_service": Provide(provide_user_service, sync_to_thread=False),
    },
    on_startup=[init_database, init_redis],
    on_shutdown=[close_redis],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
