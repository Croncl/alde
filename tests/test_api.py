from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_health_ollama_up():
    mock_info = {"online": True, "version": "0.30.8", "active_model": "alde:latest"}
    with patch(
        "app.services.ollama_service.health_check", new_callable=AsyncMock, return_value=mock_info
    ):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["ollama_online"] is True
        assert data["model_loaded"] == "alde:latest"


def test_health_ollama_down():
    mock_info = {"online": False, "error": "connection refused"}
    with patch(
        "app.services.ollama_service.health_check", new_callable=AsyncMock, return_value=mock_info
    ):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama_online"] is False


def test_chat_success():
    with patch(
        "app.services.ollama_service.generate", new_callable=AsyncMock, return_value="Use `ls -lah`"
    ):
        response = client.post("/chat", json={"message": "como listar arquivos?"})
        assert response.status_code == 200
        data = response.json()
        assert "ls" in data["response"]
        assert "session_id" in data


def test_chat_maintains_session():
    with patch(
        "app.services.ollama_service.chat_completion", new_callable=AsyncMock, return_value="ok"
    ):
        with patch(
            "app.services.ollama_service.generate", new_callable=AsyncMock, return_value="oi"
        ):
            r1 = client.post("/chat", json={"message": "oi"})
            session_id = r1.json()["session_id"]

            r2 = client.post("/chat", json={"message": "e agora?", "session_id": session_id})
            assert r2.json()["session_id"] == session_id


def test_chat_ollama_down():
    with patch(
        "app.services.ollama_service.generate",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Ollama inacessível"),
    ):
        response = client.post("/chat", json={"message": "oi"})
        assert response.status_code == 503


def test_list_models():
    raw = [{"name": "alde:latest", "size": 1000000000, "modified_at": None, "details": {}}]
    with patch("app.services.ollama_service.list_models", new_callable=AsyncMock, return_value=raw):
        with patch(
            "app.services.ollama_service.get_ollama_version",
            new_callable=AsyncMock,
            return_value="0.30.8",
        ):
            response = client.get("/models")
            assert response.status_code == 200
            data = response.json()
            assert data["models"][0]["name"] == "alde:latest"
            assert "default_model" in data


def test_history_not_found():
    response = client.get("/history/sessao-inexistente-xyz")
    assert response.status_code == 404


def test_history_found():
    with patch(
        "app.services.ollama_service.chat_completion",
        new_callable=AsyncMock,
        return_value="resposta",
    ):
        sid = "test-session-history-123"
        client.post("/chat", json={"message": "teste histórico", "session_id": sid})
        hist = client.get(f"/history/{sid}")
        assert hist.status_code == 200
        data = hist.json()
        assert data["total"] > 0
        assert data["entries"][0]["role"] == "user"
