from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas import PassengerFlights
from app import service

router = APIRouter()


@router.get("/passengers/flights", response_model=list[PassengerFlights])
async def get_passengers_flights(session: AsyncSession = Depends(get_db)):
    passengers = await service.get_all_passengers(session)
    return passengers
