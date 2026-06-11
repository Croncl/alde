from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.status_code == 200


def test_health_ollama_up():
    with patch("app.services.ollama_service.is_ollama_available", return_value=True):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["ollama_connected"] is True


def test_health_ollama_down():
    with patch("app.services.ollama_service.is_ollama_available", return_value=False):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama_connected"] is False


def test_chat_success():
    with patch("app.services.ollama_service.chat", return_value="Use o comando `ls -lah`"):
        response = client.post("/chat", json={"message": "como listar arquivos?"})
        assert response.status_code == 200
        data = response.json()
        assert "ls" in data["response"]
        assert "session_id" in data


def test_chat_maintains_session():
    with patch("app.services.ollama_service.chat", return_value="ok"):
        r1 = client.post("/chat", json={"message": "oi"})
        session_id = r1.json()["session_id"]

        r2 = client.post("/chat", json={"message": "e agora?", "session_id": session_id})
        assert r2.json()["session_id"] == session_id


def test_chat_ollama_down():
    with patch("app.services.ollama_service.chat", side_effect=ConnectionError("Ollama offline")):
        response = client.post("/chat", json={"message": "oi"})
        assert response.status_code == 503


def test_list_models():
    with patch("app.services.ollama_service.list_models", return_value=[
        {"name": "llama3.2:3b", "size": 2000000000}
    ]):
        response = client.get("/models")
        assert response.status_code == 200
        assert response.json()["models"][0]["name"] == "llama3.2:3b"


def test_history_not_found():
    response = client.get("/history/sessao-inexistente-xyz")
    assert response.status_code == 404


def test_history_found():
    with patch("app.services.ollama_service.chat", return_value="resposta"):
        r = client.post("/chat", json={"message": "teste histórico"})
        sid = r.json()["session_id"]
        hist = client.get(f"/history/{sid}")
        assert hist.status_code == 200
        assert len(hist.json()["history"]) > 0
