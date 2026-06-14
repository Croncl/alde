# app/models.py
"""
Modelos Pydantic para validação de requisições e respostas da API ALDE.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class UserProfile(str, Enum):
    """
    Perfil do usuário — controla profundidade da explicação, temperatura
    e system prompt específico.
    
    ✨ ATUALIZADO: Agora inclui os perfis do frontend (padrao, infra, suporte, devops)
    mantendo compatibilidade com os perfis antigos (iniciante, avancado, debug).
    """

    # ✨ NOVOS: Perfis do frontend
    PADRAO = "padrao"
    INFRA = "infra"
    SUPORTE = "suporte"
    DEVOPS = "devops"

    # Mantém compatibilidade com perfis antigos
    INICIANTE = "iniciante"
    AVANCADO = "avancado"
    DEBUG = "debug"


class DiagnosticType(str, Enum):
    """Tipo de diagnóstico solicitado."""

    GERAL = "geral"
    HARDWARE = "hardware"
    DOCKER = "docker"
    LOGS = "logs"
    REDE = "rede"


# ---------------------------------------------------------------------------
# Modelos de Requisição
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Requisição para o endpoint /chat."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Mensagem do usuário. Pode conter logs completos do sistema.",
        examples=["comando para listar portas abertas com o processo responsável"],
    )
    session_id: str | None = Field(
        default=None,
        description="ID de sessão para manutenção de histórico. None = conversa sem estado.",
        examples=["user-abc123"],
    )
    profile: UserProfile = Field(
        default=UserProfile.PADRAO,  # ✨ MUDOU: de AVANCADO para PADRAO
        description="Perfil do usuário para ajuste de verbosidade e temperatura.",
    )
    model: str | None = Field(
        default=None,
        description="Sobrescreve o modelo padrão. None = usa DEFAULT_MODEL do config.",
        examples=["alde", "qwen2.5-coder:1.5b"],
    )
    stream: bool = Field(
        default=False,
        description="Se True, retorna a resposta como stream SSE.",
    )

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("A mensagem não pode ser apenas espaços em branco.")
        return v


class LogAnalysisRequest(BaseModel):
    """Requisição dedicada para análise de logs longos."""

    log_content: str = Field(
        ...,
        min_length=10,
        max_length=900_000,
        description="Conteúdo completo do log para análise forense.",
    )
    session_id: str | None = None
    profile: UserProfile = UserProfile.DEBUG
    context: str = Field(
        default="",
        description="Contexto adicional: versão do kernel, serviço afetado, quando ocorreu.",
    )
    diagnostic_type: DiagnosticType = DiagnosticType.LOGS


class DockerDiagnosticRequest(BaseModel):
    """Requisição para diagnóstico de problemas Docker/Compose."""

    problem_description: str = Field(..., min_length=10)
    docker_logs: str | None = Field(default=None, description="Saída de `docker logs <container>`")
    docker_inspect: str | None = Field(
        default=None, description="Saída de `docker inspect <container>`"
    )
    compose_content: str | None = Field(default=None, description="Conteúdo do docker-compose.yml")
    session_id: str | None = None
    profile: UserProfile = UserProfile.DEVOPS  # ✨ MUDOU: de AVANCADO para DEVOPS


class HardwareDiagnosticRequest(BaseModel):
    """Requisição para diagnóstico de hardware e drivers."""

    problem_description: str = Field(..., min_length=10)
    hw_output: str | None = Field(
        default=None, description="Saída de lshw, lspci, dmesg, journalctl"
    )
    kernel_version: str | None = Field(default=None, examples=["6.1.0-21-amd64"])
    distro: str | None = Field(default=None, examples=["Debian GNU/Linux 12 (bookworm)"])
    session_id: str | None = None
    profile: UserProfile = UserProfile.INFRA  # ✨ MUDOU: de AVANCADO para INFRA


# ---------------------------------------------------------------------------
# Modelos de Resposta
# ---------------------------------------------------------------------------


class ChatResponse(BaseModel):
    """Resposta padrão de qualquer endpoint de chat."""

    response: str = Field(..., description="Resposta gerada pelo modelo.")
    model_used: str = Field(..., description="Nome do modelo Ollama utilizado.")
    session_id: str | None = None
    tokens_estimated: int | None = Field(
        default=None,
        description="Estimativa de tokens consumidos (len(texto)//4).",
    )


class HealthResponse(BaseModel):
    """Resposta do endpoint /health."""

    status: str = Field(..., examples=["ok", "degraded", "error"])
    ollama_online: bool
    model_loaded: str | None = None
    version: str = "1.0.0"
    details: dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    """Informações de um modelo disponível no Ollama."""

    name: str
    size_bytes: int | None = None
    modified_at: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ModelsResponse(BaseModel):
    """Resposta do endpoint /models."""

    models: list[ModelInfo]
    default_model: str
    ollama_version: str | None = None


class HistoryEntry(BaseModel):
    """Entrada do histórico de uma sessão."""

    role: str = Field(..., examples=["user", "assistant"])
    content: str
    timestamp: str | None = None


class HistoryResponse(BaseModel):
    """Resposta do endpoint /history/{session_id}."""

    session_id: str
    entries: list[HistoryEntry]
    total: int


class ErrorResponse(BaseModel):
    """Resposta de erro padronizado."""

    error: str
    detail: str | None = None
    code: int = 500