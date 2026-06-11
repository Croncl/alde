from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensagem do usuário")
    session_id: Optional[str] = Field(None, description="ID da sessão para manter histórico")
    model: Optional[str] = Field(None, description="Modelo Ollama a usar (padrão: configurado no .env)")
    profile: Optional[str] = Field("default", description="Perfil do usuário: iniciante, avançado, debug")


class ChatResponse(BaseModel):
    response: str
    session_id: str
    model: str


class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    version: str = "1.0.0"


class ModelInfo(BaseModel):
    name: str
    size: Optional[int] = None
    modified_at: Optional[str] = None


class ModelsResponse(BaseModel):
    models: list[ModelInfo]
