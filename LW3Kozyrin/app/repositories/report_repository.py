from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.report import Report
from app.schemas.report_schema import ReportCreate
from typing import List
from datetime import date


class ReportRepository:
    """Репозиторий для работы с отчетами в базе данных"""

    async def get_by_date(self, session: AsyncSession, report_date: date) -> List[Report]:
        """
        Получить все отчеты за конкретную дату

        Args:
            session: Сессия базы данных
            report_date: Дата отчета

        Returns:
            Список отчетов
        """
        result = await session.execute(
            select(Report).where(Report.report_at == report_date)
        )
        return list(result.scalars().all())

    async def get_all(
            self,
            session: AsyncSession,
            count: int = 10,
            page: int = 1
    ) -> List[Report]:
        """Получить все отчеты с пагинацией"""
        offset = (page - 1) * count
        result = await session.execute(
            select(Report)
            .order_by(Report.report_at.desc())
            .offset(offset)
            .limit(count)
        )
        return list(result.scalars().all())

    async def get_total_count(self, session: AsyncSession) -> int:
        """Получить общее количество отчетов"""
        result = await session.execute(select(func.count(Report.id)))
        return result.scalar_one()

    async def create(self, session: AsyncSession, report_data: ReportCreate) -> Report:
        """
        Создать новый отчет

        Args:
            session: Сессия базы данных
            report_data: Данные для создания отчета

        Returns:
            Созданный отчет
        """
        report = Report(
            report_at=report_data.report_at,
            order_id=report_data.order_id,
            count_product=report_data.count_product
        )
        session.add(report)
        await session.commit()
        await session.refresh(report)
        return report

    async def delete_by_date(self, session: AsyncSession, report_date: date) -> int:
        """
        Удалить все отчеты за конкретную дату

        Args:
            session: Сессия базы данных
            report_date: Дата отчета

        Returns:
            Количество удаленных записей
        """
        result = await session.execute(
            select(Report).where(Report.report_at == report_date)
        )
        reports = result.scalars().all()

        count = 0
        for report in reports:
            await session.delete(report)
            count += 1

        await session.commit()
        return count
