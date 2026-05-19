from contextlib import asynccontextmanager
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.database import engine, Base
from app import models  # noqa: F401
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.model = SentenceTransformer(settings.sentence_transformer_model)

    yield

    await engine.dispose()


app = FastAPI(
    title="Analysis-service",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}