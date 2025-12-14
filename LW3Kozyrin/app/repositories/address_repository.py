from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.address import Address
from app.schemas.address_schema import AddressCreate, AddressUpdate
from typing import Optional, List


class AddressRepository:
    """Репозиторий для работы с адресами в базе данных"""

    async def get_by_id(self, session: AsyncSession, address_id: int) -> Optional[Address]:
        """Получить адрес по ID"""
        result = await session.execute(
            select(Address).where(Address.id == address_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, session: AsyncSession, user_id: int) -> List[Address]:
        """Получить все адреса пользователя"""
        result = await session.execute(
            select(Address).where(Address.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_filter(
        self, 
        session: AsyncSession, 
        count: int = 10, 
        page: int = 1, 
        **kwargs
    ) -> List[Address]:
        """Получить список адресов с пагинацией"""
        query = select(Address)
        
        if "user_id" in kwargs and kwargs["user_id"]:
            query = query.where(Address.user_id == kwargs["user_id"])
        if "city" in kwargs and kwargs["city"]:
            query = query.where(Address.city.ilike(f"%{kwargs['city']}%"))
        
        offset = (page - 1) * count
        query = query.offset(offset).limit(count)
        
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_total_count(self, session: AsyncSession) -> int:
        """Получить общее количество адресов"""
        result = await session.execute(select(func.count(Address.id)))
        return result.scalar_one()

    async def create(self, session: AsyncSession, address_data: AddressCreate) -> Address:
        """Создать новый адрес"""
        address = Address(
            street=address_data.street,
            city=address_data.city,
            state=address_data.state,
            zip_code=address_data.zip_code,
            country=address_data.country,
            user_id=address_data.user_id
        )
        session.add(address)
        await session.commit()
        await session.refresh(address)
        return address

    async def update(
        self, 
        session: AsyncSession, 
        address_id: int, 
        address_data: AddressUpdate
    ) -> Optional[Address]:
        """Обновить данные адреса"""
        address = await self.get_by_id(session, address_id)
        if not address:
            return None
        
        update_data = address_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(address, field, value)
        
        await session.commit()
        await session.refresh(address)
        return address

    async def delete(self, session: AsyncSession, address_id: int) -> bool:
        """Удалить адрес"""
        address = await self.get_by_id(session, address_id)
        if not address:
            return False
        
        await session.delete(address)
        await session.commit()
        return True
