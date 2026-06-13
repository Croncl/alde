# app/services/ollama_service.py
"""
Integração com a API local do Ollama.
Responsabilidades:
  - Resolução do modelo disponível (fallback automático)
  - Geração de completions (streaming e batch)
  - Health check do servidor Ollama
  - Listagem de modelos instalados
"""

from __future__ import annotations

import json
import logging
import os
from typing import AsyncGenerator

import httpx

from knowledge_base.prompts_config import (
    DEFAULT_MODEL,
    GENERATION_PARAMS,
    MODEL_PREFERENCE,
    PROFILE_OVERRIDES,
    SESSION_SYSTEM_PREFIX,
)

logger = logging.getLogger("alde.ollama")

# Lê a URL do ambiente para funcionar tanto local quanto dentro do Docker
# docker-compose define: OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

_CONNECT_TIMEOUT: float = 5.0
_READ_TIMEOUT: float = 300.0  # logs longos podem demorar na 1ª geração


# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------


def _build_options(profile: str) -> dict:
    """Mescla parâmetros base com overrides do perfil de usuário."""
    opts = dict(GENERATION_PARAMS)
    opts.update(PROFILE_OVERRIDES.get(profile, {}))
    return opts


async def _get_installed_models(client: httpx.AsyncClient) -> list[str]:
    """Retorna lista de nomes de modelos instalados no Ollama."""
    try:
        r = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=_CONNECT_TIMEOUT)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


async def resolve_model(client: httpx.AsyncClient) -> str:
    """
    Percorre MODEL_PREFERENCE e retorna o primeiro modelo instalado.
    Garante funcionamento mesmo se 'alde' ainda não foi criado via Modelfile.
    """
    installed = await _get_installed_models(client)
    for candidate in MODEL_PREFERENCE:
        prefix = candidate.split(":")[0]
        for name in installed:
            if name == candidate or name.startswith(prefix):
                logger.info("Modelo resolvido: %s (candidato: %s)", name, candidate)
                return name
    logger.warning("Nenhum modelo preferido encontrado. Usando default: %s", DEFAULT_MODEL)
    return DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------


async def health_check() -> dict:
    """Verifica se o servidor Ollama está acessível e retorna o modelo ativo."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/version", timeout=_CONNECT_TIMEOUT)
            r.raise_for_status()
            model = await resolve_model(client)
            return {
                "online": True,
                "version": r.json().get("version", "unknown"),
                "active_model": model,
            }
        except httpx.ConnectError:
            return {"online": False, "error": f"Ollama não acessível em {OLLAMA_BASE_URL}"}
        except Exception as exc:
            return {"online": False, "error": str(exc)}


async def list_models() -> list[dict]:
    """Retorna metadados de todos os modelos instalados."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=_CONNECT_TIMEOUT)
            r.raise_for_status()
            return r.json().get("models", [])
        except Exception as exc:
            logger.error("Falha ao listar modelos: %s", exc)
            return []


async def get_ollama_version() -> str | None:
    """Retorna a versão do Ollama ou None se offline."""
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/version", timeout=_CONNECT_TIMEOUT)
            r.raise_for_status()
            return r.json().get("version")
        except Exception:
            return None


async def generate(
    prompt: str,
    model: str | None = None,
    profile: str = "avancado",
    system: str | None = None,
) -> str:
    """
    Geração batch (não-streaming). Aguarda a resposta completa antes de retornar.

    Args:
        prompt:  Texto de entrada do usuário.
        model:   Nome do modelo. None = resolução automática.
        profile: Perfil do usuário para ajuste de parâmetros.
        system:  System prompt adicional de sessão (concatenado ao do Modelfile).

    Returns:
        Texto de resposta gerado.

    Raises:
        RuntimeError: Se o Ollama retornar erro ou estiver inacessível.
    """
    async with httpx.AsyncClient() as client:
        resolved_model = model or await resolve_model(client)
        options = _build_options(profile)

        effective_system = SESSION_SYSTEM_PREFIX
        if system:
            effective_system = f"{SESSION_SYSTEM_PREFIX}\n\n{system}"

        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "system": effective_system,
            "stream": False,
            "options": options,
        }

        logger.debug(
            "generate() → model=%s profile=%s ctx=%d chars",
            resolved_model,
            profile,
            len(prompt),
        )

        try:
            r = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=httpx.Timeout(
                    connect=_CONNECT_TIMEOUT, read=_READ_TIMEOUT, write=30.0, pool=5.0
                ),
            )
            r.raise_for_status()
            return r.json().get("response", "").strip()

        except httpx.ConnectError:
            raise RuntimeError(
                f"Ollama inacessível em {OLLAMA_BASE_URL}. "
                "Execute: systemctl start ollama  ou  ollama serve"
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                "Timeout aguardando resposta do Ollama. "
                "Considere reduzir o tamanho do input ou aumentar READ_TIMEOUT."
            )
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama retornou HTTP {exc.response.status_code}: {exc.response.text}"
            )


async def generate_stream(
    prompt: str,
    model: str | None = None,
    profile: str = "avancado",
    system: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Geração streaming. Yield de cada token/chunk à medida que chega.
    Ideal para respostas longas de análise de logs.
    """
    async with httpx.AsyncClient() as client:
        resolved_model = model or await resolve_model(client)
        options = _build_options(profile)

        effective_system = SESSION_SYSTEM_PREFIX
        if system:
            effective_system = f"{SESSION_SYSTEM_PREFIX}\n\n{system}"

        payload = {
            "model": resolved_model,
            "prompt": prompt,
            "system": effective_system,
            "stream": True,
            "options": options,
        }

        try:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=httpx.Timeout(
                    connect=_CONNECT_TIMEOUT, read=_READ_TIMEOUT, write=30.0, pool=5.0
                ),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        text = chunk.get("response", "")
                        if text:
                            yield text
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue

        except httpx.ConnectError:
            yield f"[ERRO] Ollama inacessível em {OLLAMA_BASE_URL}. Execute: ollama serve"
        except httpx.TimeoutException:
            yield "[ERRO] Timeout no stream. Input muito grande ou modelo sobrecarregado."


async def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    profile: str = "avancado",
    system: str | None = None,
) -> str:
    """
    Usa o endpoint /api/chat (mantém histórico via messages[]).
    Formato de messages: [{"role": "user"|"assistant", "content": "..."}]
    """
    async with httpx.AsyncClient() as client:
        resolved_model = model or await resolve_model(client)
        options = _build_options(profile)

        system_content = SESSION_SYSTEM_PREFIX
        if system:
            system_content = f"{SESSION_SYSTEM_PREFIX}\n\n{system}"

        if not messages or messages[0].get("role") != "system":
            messages = [{"role": "system", "content": system_content}] + messages

        payload = {
            "model": resolved_model,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        try:
            r = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                timeout=httpx.Timeout(
                    connect=_CONNECT_TIMEOUT, read=_READ_TIMEOUT, write=30.0, pool=5.0
                ),
            )
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "").strip()

        except httpx.ConnectError:
            raise RuntimeError(f"Ollama inacessível em {OLLAMA_BASE_URL}.")
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Ollama HTTP {exc.response.status_code}: {exc.response.text}")
