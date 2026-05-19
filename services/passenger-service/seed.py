import random
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Flight

AIRPORTS = ["SVO", "LED", "AER", "DME", "KZN", "UFA", "OVB", "SVX"]
SEAT_CLASSES = ["economy", "business", "first"]
GENDERS = ["male", "female"]
N_PASSENGERS = 50


def _random_flight() -> dict:
    origin = random.choice(AIRPORTS)
    destination = random.choice([a for a in AIRPORTS if a != origin])

    departure = date.today() - timedelta(days=random.randint(0, 365))
    booking_advance = random.randint(1, 90)
    booking = departure - timedelta(days=booking_advance)

    return {
        "origin":         origin,
        "destination":    destination,
        "departure_date": str(departure),
        "booking_date":   str(booking),
        "seat_class":     random.choice(SEAT_CLASSES),
        "revenue_usd":    round(random.uniform(50.0, 1500.0), 2),
    }


async def seed_database(session: AsyncSession) -> None:
    count = await session.scalar(select(func.count()).select_from(Flight))
    if count > 0:
        return

    passengers = [
        Flight(
            profile_id=uuid.uuid4(),
            gender=random.choice(GENDERS),
            age=random.randint(18, 80),
            flights=[_random_flight() for _ in range(random.randint(1, 5))],
        )
        for _ in range(N_PASSENGERS)
    ]

    session.add_all(passengers)
    await session.commit()
