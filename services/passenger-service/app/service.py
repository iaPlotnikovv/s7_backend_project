from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Flight


async def get_all_passengers(session: AsyncSession) -> list[Flight]:
    result = await session.execute(select(Flight))
    return result.scalars().all()
