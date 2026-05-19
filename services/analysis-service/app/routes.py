from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.schemas import AnalysisResult
import app.ml_service as ml_service

router = APIRouter()


@router.post("/analysis", response_model=list[AnalysisResult])
async def run_analysis(
    request: Request,
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    model = request.app.state.model
    return await ml_service.run_analysis(session, model)


@router.get("/analysis/results", response_model=list[AnalysisResult])
async def get_results(
    session: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user),
):
    return await ml_service.get_all_results(session)