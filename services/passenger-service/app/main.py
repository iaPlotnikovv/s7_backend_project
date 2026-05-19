from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import engine, Base, async_session_maker
from app import models  # noqa: F401
from app.routes import router
from seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_maker() as session:
        await seed_database(session)
    yield
    await engine.dispose()


app = FastAPI(title="Passenger-service", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
