# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models import (
    ChatRequest, ChatResponse, HistoryResponse,
    LogAnalysisRequest, DockerDiagnosticRequest, HardwareDiagnosticRequest,
)
from app.services import chat_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, summary="Enviar mensagem ao assistente")
async def send_message(request: ChatRequest):
    """
    Envia uma mensagem ao ALDE e recebe uma resposta.
    - **message**: Texto da sua pergunta ou comando Linux
    - **session_id**: Opcional. Reutilize para manter contexto entre mensagens
    - **model**: Opcional. Escolha o modelo Ollama (padrão: definido em prompts_config.py)
    - **profile**: Perfil de resposta: `iniciante`, `avancado`, `debug`
    - **stream**: Se True, retorna resposta como stream SSE
    """
    if request.stream:
        async def event_generator():
            async for chunk in chat_service.chat_stream(request):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    try:
        return await chat_service.chat(request)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


@router.post("/analyze/logs", response_model=ChatResponse, summary="Análise forense de logs")
async def analyze_logs(request: LogAnalysisRequest):
    """Envia um log completo para análise estruturada."""
    try:
        return await chat_service.analyze_logs(request)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


@router.post("/diagnose/docker", response_model=ChatResponse, summary="Diagnóstico Docker/Compose")
async def diagnose_docker(request: DockerDiagnosticRequest):
    """Diagnóstico estruturado de problemas Docker/Compose."""
    try:
        return await chat_service.diagnose_docker(request)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


@router.post("/diagnose/hardware", response_model=ChatResponse, summary="Diagnóstico de hardware/drivers")
async def diagnose_hardware(request: HardwareDiagnosticRequest):
    """Diagnóstico estruturado de problemas de hardware e drivers."""
    try:
        return await chat_service.diagnose_hardware(request)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {e}")


@router.get("/history/{session_id}", response_model=HistoryResponse, summary="Histórico da sessão")
async def get_history(session_id: str):
    """Retorna o histórico de mensagens de uma sessão."""
    entries = chat_service.get_history(session_id)
    if not entries:
        raise HTTPException(status_code=404, detail="Sessão não encontrada ou vazia.")
    return HistoryResponse(session_id=session_id, entries=entries, total=len(entries))


@router.delete("/history/{session_id}", summary="Limpar sessão")
async def clear_history(session_id: str):
    """Remove o histórico de uma sessão."""
    if not chat_service.get_history(session_id):
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    chat_service.clear_history(session_id)
    return {"message": f"Sessão {session_id} removida com sucesso."}