import os
import requests
from typing import Optional

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


def is_ollama_available() -> bool:
    """Verifica se o Ollama está acessível."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def list_models() -> list[dict]:
    """Retorna modelos disponíveis no Ollama."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        return resp.json().get("models", [])
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Erro ao conectar ao Ollama: {e}")


def chat(
    messages: list[dict],
    model: Optional[str] = None,
    stream: bool = False,
) -> str:
    """
    Envia mensagens ao Ollama e retorna a resposta.

    Args:
        messages: Lista de mensagens no formato [{"role": "...", "content": "..."}]
        model: Nome do modelo Ollama. Usa DEFAULT_MODEL se não informado.
        stream: Se True, retorna gerador de chunks. Padrão False.

    Returns:
        Texto de resposta do modelo.
    """
    model = model or DEFAULT_MODEL
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            timeout=600,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Ollama não está acessível. Verifique se o serviço está rodando.")
    except requests.exceptions.Timeout:
        raise TimeoutError("Ollama demorou demais para responder. Tente um modelo mais leve.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Erro HTTP do Ollama: {e}")
