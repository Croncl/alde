from fastapi import APIRouter, HTTPException
from app.models import ModelsResponse, ModelInfo
from app.services import ollama_service

router = APIRouter()


@router.get("/models", response_model=ModelsResponse, summary="Modelos disponíveis")
def list_models():
    """Lista todos os modelos Ollama instalados localmente."""
    try:
        raw_models = ollama_service.list_models()
        models = [
            ModelInfo(
                name=m.get("name", ""),
                size=m.get("size"),
                modified_at=m.get("modified_at"),
            )
            for m in raw_models
        ]
        return ModelsResponse(models=models)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
