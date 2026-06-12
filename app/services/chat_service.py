# app/services/chat_service.py
"""
Lógica de conversação do ALDE.
Responsabilidades:
  - Gerenciamento de histórico de sessão (in-memory)
  - Construção de prompts de diagnóstico estruturado
  - Roteamento para templates corretos (logs, docker, hardware, chat geral)
  - Estimativa de tokens para alertar sobre limites de contexto
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import AsyncGenerator

from app.models import (
    ChatRequest,
    ChatResponse,
    DockerDiagnosticRequest,
    HardwareDiagnosticRequest,
    HistoryEntry,
    LogAnalysisRequest,
)
from app.services import ollama_service
from knowledge_base.prompts_config import (
    CONTEXT_COLLECTION_COMMANDS,
    DIAGNOSTIC_PROMPT_TEMPLATE,
    DOCKER_DIAGNOSE_TEMPLATE,
    HARDWARE_DIAGNOSE_TEMPLATE,
)

logger = logging.getLogger("alde.chat")

# ---------------------------------------------------------------------------
# Armazenamento de histórico em memória
# ---------------------------------------------------------------------------
_session_store: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY_ENTRIES: int = 40
MAX_HISTORY_CHARS:   int = 80_000

# Limite de aviso de contexto (128k tokens ≈ 512_000 chars)
CONTEXT_WARN_CHARS: int = 400_000


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _truncate_history(session_id: str) -> None:
    entries = _session_store[session_id]
    if len(entries) > MAX_HISTORY_ENTRIES:
        entries = entries[-MAX_HISTORY_ENTRIES:]
    total_chars = sum(len(e["content"]) for e in entries)
    while total_chars > MAX_HISTORY_CHARS and len(entries) > 2:
        removed = entries.pop(0)
        total_chars -= len(removed["content"])
    _session_store[session_id] = entries


def _build_messages_from_history(session_id: str, new_message: str) -> list[dict]:
    history = _session_store.get(session_id, [])
    messages = [{"role": e["role"], "content": e["content"]} for e in history]
    messages.append({"role": "user", "content": new_message})
    return messages


def _store_exchange(session_id: str, user_msg: str, assistant_msg: str) -> None:
    ts = time.time()
    _session_store[session_id].append({"role": "user",      "content": user_msg,      "ts": ts})
    _session_store[session_id].append({"role": "assistant", "content": assistant_msg, "ts": ts})
    _truncate_history(session_id)


def _warn_if_large_input(text: str, context: str = "") -> None:
    chars = len(text)
    tokens_est = _estimate_tokens(text)
    if chars > CONTEXT_WARN_CHARS:
        logger.warning(
            "Input grande detectado %s: %d chars (~%d tokens). "
            "Próximo do limite de contexto. Considere dividir o log.",
            context, chars, tokens_est,
        )
    else:
        logger.debug("Input %s: %d chars (~%d tokens)", context, chars, tokens_est)


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------

async def chat(request: ChatRequest) -> ChatResponse:
    """Handler principal de chat. Suporta sessões com histórico."""
    _warn_if_large_input(request.message, "chat")

    try:
        if request.session_id:
            messages = _build_messages_from_history(request.session_id, request.message)
            response_text = await ollama_service.chat_completion(
                messages=messages,
                model=request.model,
                profile=request.profile.value,
            )
            _store_exchange(request.session_id, request.message, response_text)
        else:
            response_text = await ollama_service.generate(
                prompt=request.message,
                model=request.model,
                profile=request.profile.value,
            )

        return ChatResponse(
            response=response_text,
            model_used=request.model or "alde",
            session_id=request.session_id,
            tokens_estimated=_estimate_tokens(request.message + response_text),
        )

    except RuntimeError as exc:
        raise exc


async def chat_stream(request: ChatRequest) -> AsyncGenerator[str, None]:
    """Versão streaming do chat. Yields chunks de texto."""
    _warn_if_large_input(request.message, "chat_stream")

    full_response: list[str] = []

    async for chunk in ollama_service.generate_stream(
        prompt=request.message,
        model=request.model,
        profile=request.profile.value,
    ):
        full_response.append(chunk)
        yield chunk

    if request.session_id:
        _store_exchange(request.session_id, request.message, "".join(full_response))


async def analyze_logs(request: LogAnalysisRequest) -> ChatResponse:
    """Análise forense de logs longos com template de diagnóstico estruturado."""
    _warn_if_large_input(request.log_content, "log_analysis")

    prompt = DIAGNOSTIC_PROMPT_TEMPLATE.format(
        profile=request.profile.value,
        context=request.context or "Não informado",
        log_content=request.log_content,
    )

    logger.info(
        "Iniciando análise de log: %d chars (~%d tokens)",
        len(request.log_content),
        _estimate_tokens(request.log_content),
    )

    response_text = await ollama_service.generate(
        prompt=prompt,
        model=None,
        profile=request.profile.value,
    )

    if request.session_id:
        _store_exchange(
            request.session_id,
            f"[LOG ANALYSIS] {len(request.log_content)} chars",
            response_text,
        )

    return ChatResponse(
        response=response_text,
        model_used="alde",
        session_id=request.session_id,
        tokens_estimated=_estimate_tokens(prompt + response_text),
    )


async def diagnose_docker(request: DockerDiagnosticRequest) -> ChatResponse:
    """Diagnóstico estruturado de problemas Docker/Compose."""
    prompt = DOCKER_DIAGNOSE_TEMPLATE.format(
        problem=request.problem_description,
        docker_output=(request.docker_logs or "") + "\n" + (request.docker_inspect or ""),
        compose_content=request.compose_content or "Não fornecido",
    )

    response_text = await ollama_service.generate(
        prompt=prompt,
        model=None,                     # usa resolução automática
        profile=request.profile.value,
    )

    if request.session_id:
        _store_exchange(request.session_id, request.problem_description, response_text)

    return ChatResponse(
        response=response_text,
        model_used="alde",
        session_id=request.session_id,
        tokens_estimated=_estimate_tokens(prompt + response_text),
    )


async def diagnose_hardware(request: HardwareDiagnosticRequest) -> ChatResponse:
    """Diagnóstico estruturado de problemas de hardware/drivers."""
    prompt = HARDWARE_DIAGNOSE_TEMPLATE.format(
        problem=request.problem_description,
        hw_output=request.hw_output or "Não fornecido",
        kernel_version=request.kernel_version or "Desconhecido",
        distro=request.distro or "Desconhecido",
    )

    response_text = await ollama_service.generate(
        prompt=prompt,
        model=None,
        profile=request.profile.value,
    )

    if request.session_id:
        _store_exchange(request.session_id, request.problem_description, response_text)

    return ChatResponse(
        response=response_text,
        model_used="alde",
        session_id=request.session_id,
        tokens_estimated=_estimate_tokens(prompt + response_text),
    )


# ---------------------------------------------------------------------------
# Gerenciamento de histórico
# ---------------------------------------------------------------------------

def get_history(session_id: str) -> list[HistoryEntry]:
    entries = _session_store.get(session_id, [])
    return [
        HistoryEntry(
            role=e["role"],
            content=e["content"],
            timestamp=str(e.get("ts", "")),
        )
        for e in entries
    ]


def clear_history(session_id: str) -> None:
    _session_store.pop(session_id, None)
    logger.info("Histórico da sessão %s removido.", session_id)


def get_context_collection_hint(category: str) -> list[str]:
    return CONTEXT_COLLECTION_COMMANDS.get(category, [])
