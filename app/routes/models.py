# app/routes/models.py
from fastapi import APIRouter, HTTPException
from app.models import ModelsResponse, ModelInfo
from app.services import ollama_service
from knowledge_base.prompts_config import DEFAULT_MODEL

router = APIRouter()


@router.get("/models", response_model=ModelsResponse, summary="Modelos disponíveis")
async def list_models():
    """Lista todos os modelos Ollama instalados localmente."""
    try:
        raw_models = await ollama_service.list_models()
        models = [
            ModelInfo(
                name=m.get("name", ""),
                size_bytes=m.get("size"),
                modified_at=m.get("modified_at"),
                details=m.get("details", {}),
            )
            for m in raw_models
        ]
        ollama_version = await ollama_service.get_ollama_version()
        return ModelsResponse(
            models=models,
            default_model=DEFAULT_MODEL,
            ollama_version=ollama_version,
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar modelos: {e}")