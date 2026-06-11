from fastapi import APIRouter, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, summary="Enviar mensagem ao assistente")
def send_message(request: ChatRequest):
    """
    Envia uma mensagem ao ALDE e recebe uma resposta.

    - **message**: Texto da sua pergunta ou comando Linux
    - **session_id**: Opcional. Reutilize para manter contexto entre mensagens
    - **model**: Opcional. Escolha o modelo Ollama (padrão: llama3.2:3b)
    - **profile**: Perfil de resposta: `default`, `iniciante`, `avancado`, `debug`
    """
    try:
        response, session_id = chat_service.process_message(
            message=request.message,
            session_id=request.session_id,
            model=request.model,
            profile=request.profile or "default",
        )
        return ChatResponse(
            response=response,
            session_id=session_id,
            model=request.model or "llama3.2:3b",
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


@router.get("/history/{session_id}", summary="Histórico da sessão")
def get_history(session_id: str):
    """Retorna o histórico de mensagens de uma sessão."""
    history = chat_service.get_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou vazia.")
    return {"session_id": session_id, "history": history}


@router.delete("/history/{session_id}", summary="Limpar sessão")
def clear_history(session_id: str):
    """Remove o histórico de uma sessão."""
    cleared = chat_service.clear_session(session_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return {"message": f"Sessão {session_id} removida com sucesso."}
