import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from app.services import ollama_service
from app.utils.helpers import generate_session_id, truncate_history
from knowledge_base.prompts_config import get_system_prompt

# Armazenamento em memória: {session_id: [{"role": ..., "content": ...}]}
_sessions: dict[str, list[dict]] = {}


def get_or_create_session(session_id: str | None) -> tuple[str, list[dict]]:
    """Retorna sessão existente ou cria uma nova."""
    if not session_id or session_id not in _sessions:
        session_id = generate_session_id()
        _sessions[session_id] = []
    return session_id, _sessions[session_id]


def process_message(
    message: str,
    session_id: str | None = None,
    model: str | None = None,
    profile: str = "default",
) -> tuple[str, str]:
    """
    Processa uma mensagem do usuário e retorna (resposta, session_id).

    Args:
        message: Texto da mensagem do usuário.
        session_id: ID de sessão existente (opcional).
        model: Modelo Ollama a usar.
        profile: Perfil do usuário (default, iniciante, avançado, debug).

    Returns:
        Tupla (resposta_do_modelo, session_id).
    """
    session_id, history = get_or_create_session(session_id)

    # Adiciona mensagem do usuário ao histórico
    history.append({"role": "user", "content": message})

    # Monta lista de mensagens com system prompt + histórico truncado
    system_prompt = {"role": "system", "content": get_system_prompt(profile)}
    messages = [system_prompt] + truncate_history(history)

    # Chama o Ollama
    response = ollama_service.chat(messages=messages, model=model)

    # Adiciona resposta ao histórico
    history.append({"role": "assistant", "content": response})
    _sessions[session_id] = history

    return response, session_id


def get_history(session_id: str) -> list[dict]:
    """Retorna histórico de uma sessão."""
    return _sessions.get(session_id, [])


def clear_session(session_id: str) -> bool:
    """Limpa histórico de uma sessão."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False
