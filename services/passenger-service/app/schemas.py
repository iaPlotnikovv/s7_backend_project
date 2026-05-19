import uuid
from pydantic import BaseModel, ConfigDict


class FlightItem(BaseModel):
    origin: str
    destination: str
    departure_date: str
    booking_date: str
    seat_class: str
    revenue_usd: float


class PassengerFlights(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    profile_id: uuid.UUID
    gender: str
    age: int
    flights: list[FlightItem]