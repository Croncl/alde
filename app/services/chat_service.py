# app/services/chat_service.py
"""
Lógica de conversação do ALDE.
Responsabilidades:
  - Gerenciamento de histórico de sessão (in-memory)
  - Construção de prompts de diagnóstico estruturado
  - Roteamento para templates corretos (logs, docker, hardware, chat geral)
  - Estimativa de tokens para alertar sobre limites de contexto
  - Injeção de contexto da knowledge base (retrieval) em todas as interações
  - Aplicação de system prompts específicos por perfil
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
    PROFILE_SYSTEM_PROMPTS,
    SESSION_SYSTEM_PREFIX,
)
from knowledge_base.retrieval import retrieve

logger = logging.getLogger("alde.chat")

# ---------------------------------------------------------------------------
# Armazenamento de histórico em memória
# ---------------------------------------------------------------------------
_session_store: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY_ENTRIES: int = 40
MAX_HISTORY_CHARS: int = 80_000

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
    _session_store[session_id].append({"role": "user", "content": user_msg, "ts": ts})
    _session_store[session_id].append({"role": "assistant", "content": assistant_msg, "ts": ts})
    _truncate_history(session_id)


def _warn_if_large_input(text: str, context: str = "") -> None:
    chars = len(text)
    tokens_est = _estimate_tokens(text)
    if chars > CONTEXT_WARN_CHARS:
        logger.warning(
            "Input grande detectado %s: %d chars (~%d tokens). "
            "Próximo do limite de contexto. Considere dividir o log.",
            context,
            chars,
            tokens_est,
        )
    else:
        logger.debug("Input %s: %d chars (~%d tokens)", context, chars, tokens_est)


# ---------------------------------------------------------------------------
# ✨ NOVO: Construção de system prompt por perfil + contexto da KB
# ---------------------------------------------------------------------------


def _build_system_prompt(profile: str, kb_context: str) -> str:
    """
    Constrói o system prompt completo combinando:
    1. SESSION_SYSTEM_PREFIX (base)
    2. PROFILE_SYSTEM_PROMPTS (específico do perfil)
    3. kb_context (comandos da base de conhecimento)
    """
    parts = [SESSION_SYSTEM_PREFIX]

    # Adiciona system prompt específico do perfil
    profile_prompt = PROFILE_SYSTEM_PROMPTS.get(profile)
    if profile_prompt:
        parts.append(profile_prompt)
    else:
        logger.warning("Perfil desconhecido: %s, usando padrão", profile)
        parts.append(PROFILE_SYSTEM_PROMPTS.get("padrao", ""))

    # Adiciona contexto da KB se houver
    if kb_context:
        parts.append(
            "\n\n---\n"
            "[Comandos relevantes da base de conhecimento — use como referência prioritária]:\n"
            f"{kb_context}"
        )

    return "\n\n".join(parts)


def _get_kb_context(query: str, context_label: str = "chat") -> str:
    """
    Executa o retrieval e retorna o bloco de contexto para injeção no prompt.
    Retorna string vazia se não houver matches.
    """
    try:
        kb_context = retrieve(query)
        if kb_context:
            logger.info(
                "KB retrieval [%s]: %d comandos injetados para query=%r",
                context_label,
                kb_context.count("•"),
                query[:60],
            )
        else:
            logger.debug("KB retrieval [%s]: sem match para query=%r", context_label, query[:60])
        return kb_context or ""
    except Exception as e:
        logger.error("Erro no retrieval da KB [%s]: %s", context_label, e)
        return ""


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------


async def chat(request: ChatRequest) -> ChatResponse:
    """Handler principal de chat. Suporta sessões com histórico."""
    _warn_if_large_input(request.message, "chat")

    try:
        # ✨ Retrieval da KB
        kb_context = _get_kb_context(request.message, "chat")

        # ✨ Constrói system prompt completo (base + perfil + KB)
        system_prompt = _build_system_prompt(request.profile.value, kb_context)

        if request.session_id:
            messages = _build_messages_from_history(request.session_id, request.message)

            response_text = await ollama_service.chat_completion(
                messages=messages,
                model=request.model,
                profile=request.profile.value,
                system=system_prompt,
            )
            _store_exchange(request.session_id, request.message, response_text)
        else:
            response_text = await ollama_service.generate(
                prompt=request.message,
                model=request.model,
                profile=request.profile.value,
                system=system_prompt,
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

    # ✨ Retrieval da KB (também no streaming!)
    kb_context = _get_kb_context(request.message, "chat_stream")

    # ✨ Constrói system prompt completo
    system_prompt = _build_system_prompt(request.profile.value, kb_context)

    full_response: list[str] = []

    async for chunk in ollama_service.generate_stream(
        prompt=request.message,
        model=request.model,
        profile=request.profile.value,
        system=system_prompt,
    ):
        full_response.append(chunk)
        yield chunk

    if request.session_id:
        _store_exchange(request.session_id, request.message, "".join(full_response))


async def analyze_logs(request: LogAnalysisRequest) -> ChatResponse:
    """Análise forense de logs longos com template de diagnóstico estruturado."""
    _warn_if_large_input(request.log_content, "log_analysis")

    # ✨ Retrieval baseado no contexto do problema
    kb_context = _get_kb_context(
        request.context or request.log_content[:500],
        "log_analysis",
    )

    prompt = DIAGNOSTIC_PROMPT_TEMPLATE.format(
        profile=request.profile.value,
        context=request.context or "Não informado",
        log_content=request.log_content,
    )

    # ✨ Injeta contexto da KB no prompt de diagnóstico
    if kb_context:
        prompt = f"{prompt}\n\n---\n[Comandos úteis para esta análise]:\n{kb_context}"

    # ✨ Constrói system prompt com perfil
    system_prompt = _build_system_prompt(request.profile.value, "")

    logger.info(
        "Iniciando análise de log: %d chars (~%d tokens)",
        len(request.log_content),
        _estimate_tokens(request.log_content),
    )

    response_text = await ollama_service.generate(
        prompt=prompt,
        model=None,
        profile=request.profile.value,
        system=system_prompt,
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
    # ✨ Retrieval baseado na descrição do problema
    kb_context = _get_kb_context(request.problem_description, "diagnose_docker")

    prompt = DOCKER_DIAGNOSE_TEMPLATE.format(
        problem=request.problem_description,
        docker_output=(request.docker_logs or "") + "\n" + (request.docker_inspect or ""),
        compose_content=request.compose_content or "Não fornecido",
    )

    # ✨ Injeta contexto da KB no prompt de diagnóstico
    if kb_context:
        prompt = f"{prompt}\n\n---\n[Comandos Docker relevantes]:\n{kb_context}"

    # ✨ Constrói system prompt com perfil
    system_prompt = _build_system_prompt(request.profile.value, "")

    response_text = await ollama_service.generate(
        prompt=prompt,
        model=None,
        profile=request.profile.value,
        system=system_prompt,
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
    # ✨ Retrieval baseado na descrição do problema
    kb_context = _get_kb_context(request.problem_description, "diagnose_hardware")

    prompt = HARDWARE_DIAGNOSE_TEMPLATE.format(
        problem=request.problem_description,
        hw_output=request.hw_output or "Não fornecido",
        kernel_version=request.kernel_version or "Desconhecido",
        distro=request.distro or "Desconhecido",
    )

    # ✨ Injeta contexto da KB no prompt de diagnóstico
    if kb_context:
        prompt = f"{prompt}\n\n---\n[Comandos de hardware/driver relevantes]:\n{kb_context}"

    # ✨ Constrói system prompt com perfil
    system_prompt = _build_system_prompt(request.profile.value, "")

    response_text = await ollama_service.generate(
        prompt=prompt,
        model=None,
        profile=request.profile.value,
        system=system_prompt,
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
