import os
from litestar import Litestar
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.controllers.user_controller import UserController
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.models.base import Base

# Настройка базы данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:viking676@localhost:5432/litestar_db"
)

# Создание асинхронного движка
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Логирование SQL-запросов
    future=True
)

# Создание фабрики сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def provide_db_session() -> AsyncSession:
    """
    Провайдер сессии базы данных

    Создает новую сессию для каждого запроса и автоматически закрывает её
    после завершения обработки запроса

    Yields:
        AsyncSession: Сессия базы данных
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def provide_user_repository() -> UserRepository:
    """
    Провайдер репозитория пользователей

    Returns:
        UserRepository: Экземпляр репозитория пользователей
    """
    return UserRepository()


def provide_user_service(
        user_repository: UserRepository,
        db_session: AsyncSession
) -> UserService:
    """
    Провайдер сервиса пользователей

    Args:
        user_repository: Репозиторий пользователей
        db_session: Сессия базы данных

    Returns:
        UserService: Экземпляр сервиса пользователей
    """
    return UserService(user_repository, db_session)


async def init_database() -> None:
    """
    Инициализация базы данных

    Создает все таблицы, определенные в моделях
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Создание приложения Litestar
app = Litestar(
    route_handlers=[UserController],
    dependencies={
        "db_session": Provide(provide_db_session),
        "user_repository": Provide(provide_user_repository, sync_to_thread=False),
        "user_service": Provide(provide_user_service, sync_to_thread=False),
    },
    on_startup=[init_database],  # Инициализация БД при старте приложения
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
