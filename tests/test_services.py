from unittest.mock import patch, MagicMock
from app.services import chat_service
from app.utils.helpers import generate_session_id, truncate_history


def test_generate_session_id_is_unique():
    ids = {generate_session_id() for _ in range(100)}
    assert len(ids) == 100


def test_truncate_history_keeps_last_n():
    history = [{"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(30)]
    truncated = truncate_history(history, max_turns=5)
    assert len(truncated) == 10  # 5 turns * 2 mensagens


def test_truncate_history_short_list():
    history = [{"role": "user", "content": "oi"}]
    assert truncate_history(history) == history


def test_process_message_creates_session():
    with patch("app.services.ollama_service.chat", return_value="resposta teste"):
        response, session_id = chat_service.process_message("oi")
        assert response == "resposta teste"
        assert session_id is not None


def test_process_message_reuses_session():
    with patch("app.services.ollama_service.chat", return_value="ok"):
        _, sid = chat_service.process_message("primeira")
        _, sid2 = chat_service.process_message("segunda", session_id=sid)
        assert sid == sid2


def test_get_history_returns_messages():
    with patch("app.services.ollama_service.chat", return_value="resposta"):
        _, sid = chat_service.process_message("teste get history")
        history = chat_service.get_history(sid)
        assert len(history) == 2  # user + assistant
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"


def test_clear_session():
    with patch("app.services.ollama_service.chat", return_value="ok"):
        _, sid = chat_service.process_message("mensagem para deletar")
        assert chat_service.clear_session(sid) is True
        assert chat_service.get_history(sid) == []


def test_clear_nonexistent_session():
    assert chat_service.clear_session("nao-existe-xyz") is False
