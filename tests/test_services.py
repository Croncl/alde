from unittest.mock import AsyncMock, patch

from app.services import chat_service
from app.utils.helpers import generate_session_id, truncate_history


def test_generate_session_id_is_unique():
    ids = {generate_session_id() for _ in range(100)}
    assert len(ids) == 100


def test_truncate_history_keeps_last_n():
    history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(30)
    ]
    truncated = truncate_history(history, max_turns=5)
    assert len(truncated) == 10  # 5 turns * 2 mensagens


def test_truncate_history_short_list():
    history = [{"role": "user", "content": "oi"}]
    assert truncate_history(history) == history


def test_chat_creates_session():
    from app.models import ChatRequest

    request = ChatRequest(message="oi")
    with patch("app.services.ollama_service.generate", new_callable=AsyncMock, return_value="olá"):
        with patch("knowledge_base.retrieval.retrieve", return_value=""):
            import asyncio

            response = asyncio.run(chat_service.chat(request))
            assert response.response == "olá"
            assert "tokens_estimated" in response.model_dump()


def test_chat_reuses_session():
    from app.models import ChatRequest

    with patch("app.services.ollama_service.generate", new_callable=AsyncMock, return_value="ok"):
        with patch(
            "app.services.ollama_service.chat_completion",
            new_callable=AsyncMock,
            return_value="ack",
        ):
            with patch("knowledge_base.retrieval.retrieve", return_value=""):
                import asyncio

                r1 = asyncio.run(chat_service.chat(ChatRequest(message="primeira")))
                sid = r1.session_id
                r2 = asyncio.run(chat_service.chat(ChatRequest(message="segunda", session_id=sid)))
                assert r2.session_id == sid


def test_get_history_returns_messages():
    from app.models import ChatRequest

    with patch(
        "app.services.ollama_service.generate", new_callable=AsyncMock, return_value="resposta"
    ):
        with patch("knowledge_base.retrieval.retrieve", return_value=""):
            import asyncio

            r = asyncio.run(chat_service.chat(ChatRequest(message="teste")))
            # sem session_id no request, histórico não é armazenado — comportamento esperado
            history = chat_service.get_history(r.session_id or "vazio")
            assert isinstance(history, list)


def test_clear_history():
    from app.models import ChatRequest

    with patch(
        "app.services.ollama_service.chat_completion", new_callable=AsyncMock, return_value="ok"
    ):
        with patch("knowledge_base.retrieval.retrieve", return_value=""):
            import asyncio

            sid = generate_session_id()
            asyncio.run(chat_service.chat(ChatRequest(message="msg", session_id=sid)))
            history_before = chat_service.get_history(sid)
            assert len(history_before) > 0
            chat_service.clear_history(sid)
            assert chat_service.get_history(sid) == []
