from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import chat, health, models

load_dotenv()

app = FastAPI(
    title="ALDE – Assistente Linux de Execução",
    description=(
        "API para assistente técnico Linux com modelos Ollama locais. "
        "Funciona offline, em máquinas com 4GB RAM."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Status"])
app.include_router(models.router, tags=["Modelos"])
app.include_router(chat.router, tags=["Chat"])


@app.get("/", tags=["Root"])
def root():
    return {
        "projeto": "ALDE – Assistente Linux de Execução",
        "versao": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
