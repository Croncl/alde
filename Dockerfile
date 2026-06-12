# =============================================================================
# ALDE – Assistente Linux de Diagnóstico e Execução
# Dockerfile para API FastAPI (Uvicorn) — Otimizado para Ambiente Local x86_64
# =============================================================================

FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="ALDE Project"
LABEL description="Assistente Linux de Execução – API FastAPI"

# Impede que o Python grave arquivos .pyc e garante saída de logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Criação do usuário não-root por segurança antes de definir o diretório de trabalho
RUN useradd --create-home --shell /bin/bash alde
WORKDIR /home/alde/app

# Instalação de dependências mínimas do sistema operacional (Debian-slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalação das dependências Python (Pip cache limpo para economizar espaço)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a estrutura interna de código e base de conhecimento do ALDE
COPY app/ ./app/
COPY knowledge_base/ ./knowledge_base/
COPY .env.example .env

# Ajusta as permissões da pasta para o usuário comum 'alde' ter controle dos arquivos
RUN chown -R alde:alde /home/alde/app
USER alde

# Porta nativa que o Uvicorn vai expor dentro da rede do Docker
EXPOSE 8000

# Verificação de saúde (Healthcheck) para garantir que o FastAPI está respondendo
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Inicialização oficial do servidor de aplicação ASGI (FastAPI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]