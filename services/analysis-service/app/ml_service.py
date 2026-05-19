from datetime import datetime
import numpy as np
from sklearn.cluster import KMeans
from umap import UMAP
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Result

# ------------------------------------ Сериализация данных в текст ------------------------------------

def serialize_passenger(passenger: dict) -> str:
    flights = passenger["flights"]
    gender = passenger["gender"]
    age = passenger["age"]

    flight_texts = []
    for f in flights:
        days_in_advance = (
            datetime.strptime(f['departure_date'], "%Y-%m-%d").date() -  datetime.strptime(f['booking_date'], "%Y-%m-%d").date()
        ).days
        flight_texts.append(
            f"{f['origin']} to {f['destination']}, {f['seat_class']} class, "
            f"departed {f['departure_date']}, booked {days_in_advance} days in advance, "
            f"revenue ${f['revenue_usd']}"
        )

    flights_str = ". ".join(flight_texts)
    return f"Passenger: {gender}, age {age}. Flights: {flights_str}"

# ------------------------------------ ML Pipeline ------------------------------------

def run_ml_pipeline(
    texts: list[str],
    model,  # SentenceTransformer из app.state
    n_clusters: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Возвращает (embeddings, clusters, coords) где coords.shape == (n, 2)."""

    embeddings = model.encode(texts, show_progress_bar=False)

    n_samples = len(texts)
    actual_clusters = min(n_clusters, n_samples)
    actual_neighbors = min(15, n_samples - 1)
    kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init="auto")
    clusters = kmeans.fit_predict(embeddings)

    reducer = UMAP(n_neighbors=actual_neighbors, n_components=2, random_state=42)
    coords = reducer.fit_transform(embeddings)

    return embeddings, clusters, coords

# ------------------------------------ Database ------------------------------------

async def fetch_passengers() -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f'{settings.passenger_service_url}/passengers/flights')
        response.raise_for_status()
        return response.json()


async def upsert_result(session: AsyncSession, data: dict) -> None:
    stmt = select(Result).where(Result.profile_id == data["profile_id"])
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing is None:
        session.add(Result(**data))
    else:
        for key, value in data.items():
            setattr(existing, key, value)

    await session.commit()


async def run_analysis(session: AsyncSession, model) -> list[dict]:
    passengers = await fetch_passengers()

    texts = [serialize_passenger(p) for p in passengers]
    embeddings, clusters, coords = run_ml_pipeline(
        texts, model, settings.kmeans_n_clusters
    )

    results = []
    for i, passenger in enumerate(passengers):
        data = {
            "profile_id": passenger["profile_id"],
            "serialized_text": texts[i],
            "embedding": embeddings[i].tolist(),
            "cluster": int(clusters[i]),
            "x": float(coords[i, 0]),
            "y": float(coords[i, 1]),
        }
        await upsert_result(session, data)
        results.append({k: v for k, v in data.items() if k != "embedding"})

    return results


async def get_all_results(session: AsyncSession) -> list[dict]:
    stmt = select(Result)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "profile_id": str(r.profile_id),
            "cluster": r.cluster,
            "serialized_text": r.serialized_text,
            "x": r.x,
            "y": r.y,
        }
        for r in rows
    ]