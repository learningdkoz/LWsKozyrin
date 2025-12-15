from litestar import Controller, get, post
from litestar.di import Provide
from litestar.params import Parameter
from litestar.status_codes import HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND
from litestar.response import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.report_repository import ReportRepository
from app.schemas.report_schema import ReportResponse
from typing import List, Annotated
from datetime import date


class ReportController(Controller):
    """Контроллер для работы с отчетами"""

    path = "/report"

    @get("/", status_code=HTTP_200_OK)
    async def get_reports_by_date(
            self,
            db_session: AsyncSession,
            report_repository: ReportRepository,
            report_date: Annotated[date, Parameter(description="Дата отчета в формате YYYY-MM-DD")]
    ) -> List[ReportResponse]:
        """
        Получить отчеты за конкретную дату

        Args:
            db_session: Сессия базы данных
            report_repository: Репозиторий отчетов
            report_date: Дата отчета

        Returns:
            Список отчетов за указанную дату
        """
        reports = await report_repository.get_by_date(db_session, report_date)

        if not reports:
            return Response(
                content={
                    "message": f"Отчеты за {report_date} не найдены",
                    "date": str(report_date),
                    "reports": []
                },
                status_code=HTTP_200_OK
            )

        return [ReportResponse.model_validate(report) for report in reports]

    @get("/all", status_code=HTTP_200_OK)
    async def get_all_reports(
            self,
            db_session: AsyncSession,
            report_repository: ReportRepository,
            count: int = 10,
            page: int = 1
    ) -> dict:
        """
        Получить все отчеты с пагинацией

        Args:
            db_session: Сессия базы данных
            report_repository: Репозиторий отчетов
            count: Количество записей на странице
            page: Номер страницы

        Returns:
            Словарь с отчетами и метаданными пагинации
        """
        if count <= 0:
            count = 10
        if page <= 0:
            page = 1

        reports = await report_repository.get_all(db_session, count, page)
        total = await report_repository.get_total_count(db_session)

        return {
            "reports": [ReportResponse.model_validate(report) for report in reports],
            "pagination": {
                "page": page,
                "count": count,
                "total": total,
                "pages": (total + count - 1) // count
            }
        }

    @post("/generate", status_code=HTTP_202_ACCEPTED)
    async def generate_report_manually(
            self,
            report_date: Annotated[date, Parameter(description="Дата для генерации отчета")]
    ) -> dict:
        """
        Запустить генерацию отчета за конкретную дату вручную

        Args:
            report_date: Дата для генерации отчета

        Returns:
            Статус запуска задачи
        """
        from app.scheduler.taskiq_app import generate_report_for_date

        try:
            # Запускаем задачу асинхронно через TaskIQ
            task = await generate_report_for_date.kiq(target_date=str(report_date))

            return {
                "status": "scheduled",
                "message": f"Генерация отчета за {report_date} запланирована",
                "task_id": task.task_id,
                "date": str(report_date)
            }
        except Exception as e:
            return Response(
                content={
                    "status": "error",
                    "message": f"Ошибка при запуске задачи: {str(e)}",
                    "date": str(report_date)
                },
                status_code=500
            )
