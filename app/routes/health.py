from fastapi import APIRouter
from app.models import HealthResponse
from app.services import ollama_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Status da API")
def health_check():
    """Verifica se a API e o Ollama estão operacionais."""
    ollama_ok = ollama_service.is_ollama_available()
    return HealthResponse(
        status="ok" if ollama_ok else "degraded",
        ollama_connected=ollama_ok,
    )
