import uuid
from datetime import datetime


def generate_session_id() -> str:
    """Gera um ID único de sessão."""
    return str(uuid.uuid4())


def get_timestamp() -> str:
    """Retorna timestamp atual em ISO format."""
    return datetime.utcnow().isoformat()


def truncate_history(history: list, max_turns: int = 10) -> list:
    """
    Limita o histórico para evitar contexto excessivo em modelos leves.
    Mantém as últimas `max_turns` trocas (user + assistant).
    """
    if len(history) > max_turns * 2:
        return history[-(max_turns * 2):]
    return history
