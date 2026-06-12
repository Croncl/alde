# app/routes/health.py
from fastapi import APIRouter
from app.models import HealthResponse
from app.services import ollama_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Status da API")
async def health_check():
    """Verifica se a API e o Ollama estão operacionais."""
    info = await ollama_service.health_check()
    return HealthResponse(
        status="ok" if info["online"] else "degraded",
        ollama_online=info["online"],
        model_loaded=info.get("active_model"),
        details={"version": info.get("version"), "error": info.get("error")},
    )