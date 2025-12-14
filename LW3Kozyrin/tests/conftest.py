"""
Конфигурация pytest и общие фикстуры для тестирования

Фикстуры:
    - engine: Создает тестовый движок SQLite in-memory
    - test_session: Предоставляет сессию БД для каждого теста
    - user_repository: Репозиторий пользователей
    - product_repository: Репозиторий продуктов
    - address_repository: Репозиторий адресов
    - order_repository: Репозиторий заказов
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.models.base import Base
from app.repositories.user_repository import UserRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.address_repository import AddressRepository
from app.repositories.order_repository import OrderRepository


@pytest_asyncio.fixture(scope="function")
async def engine():
    """
    Фикстура для создания тестового движка базы данных

    Использует SQLite in-memory для изоляции тестов и быстрой работы.
    Каждый тест получает чистую базу данных.

    Yields:
        AsyncEngine: Асинхронный движок базы данных
    """
    # Создаем in-memory SQLite БД для тестов
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Отключаем логирование SQL для чистоты вывода тестов
    )

    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Очищаем после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(engine):
    """
    Фикстура для создания тестовой сессии БД

    Каждый тест получает свою изолированную сессию.
    После теста все изменения откатываются.

    Args:
        engine: Движок базы данных из фикстуры engine

    Yields:
        AsyncSession: Сессия базы данных для теста
    """
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_factory() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture(scope="function")
def user_repository():
    """
    Фикстура для создания репозитория пользователей

    Returns:
        UserRepository: Экземпляр репозитория пользователей
    """
    return UserRepository()


@pytest.fixture(scope="function")
def product_repository():
    """
    Фикстура для создания репозитория продуктов

    Returns:
        ProductRepository: Экземпляр репозитория продуктов
    """
    return ProductRepository()


@pytest.fixture(scope="function")
def address_repository():
    """
    Фикстура для создания репозитория адресов

    Returns:
        AddressRepository: Экземпляр репозитория адресов
    """
    return AddressRepository()


@pytest.fixture(scope="function")
def order_repository():
    """
    Фикстура для создания репозитория заказов

    Returns:
        OrderRepository: Экземпляр репозитория заказов
    """
    return OrderRepository()
