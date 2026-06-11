FROM python:3.11-slim

# Metadados
LABEL maintainer="ALDE Project"
LABEL description="Assistente Linux de Execução – API FastAPI"

# Usuário não-root por segurança
RUN useradd --create-home --shell /bin/bash alde
WORKDIR /home/alde/app

# Dependências do sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código
COPY app/ ./app/
COPY knowledge_base/ ./knowledge_base/
COPY .env.example .env

# Ajusta permissões
RUN chown -R alde:alde /home/alde/app
USER alde

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
