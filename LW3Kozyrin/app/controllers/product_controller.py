"""Контроллер для работы с продуктами через REST API"""
from litestar import Controller, get
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.product_repository import ProductRepository
from app.schemas.product_schema import ProductResponse, ProductListResponse
from typing import Optional


class ProductController(Controller):
    """Контроллер для HTTP endpoints продуктов"""
    path = "/products"

    @get("/{product_id:int}")
    async def get_product(
            self,
            product_id: int,
            db_session: AsyncSession,
            product_repository: ProductRepository
    ) -> ProductResponse:
        """
        Получить продукт по ID

        Args:
            product_id: ID продукта
        """
        product = await product_repository.get_by_id(db_session, product_id)
        if not product:
            from litestar.exceptions import NotFoundException
            raise NotFoundException(f"Продукт с ID {product_id} не найден")
        return ProductResponse.model_validate(product)

    @get("/")
    async def get_all_products(
            self,
            db_session: AsyncSession,
            product_repository: ProductRepository,
            count: int = 10,
            page: int = 1,
            name: Optional[str] = None,
            min_price: Optional[float] = None,
            max_price: Optional[float] = None,
    ) -> ProductListResponse:
        """
        Получить список продуктов с фильтрацией и пагинацией

        Args:
            count: Количество записей на странице
            page: Номер страницы
            name: Фильтр по названию
            min_price: Минимальная цена
            max_price: Максимальная цена
        """
        products = await product_repository.get_by_filter(
            db_session,
            count=count,
            page=page,
            name=name,
            min_price=min_price,
            max_price=max_price
        )
        total_count = await product_repository.get_total_count(db_session)

        return ProductListResponse(
            products=[ProductResponse.model_validate(p) for p in products],
            total_count=total_count
        )
