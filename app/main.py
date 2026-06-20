import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes import chat, health, models

load_dotenv()

app = FastAPI(
    title="ALDE – Assistente Linux de Diagnóstico e Execução",
    description=(
        "API para assistente técnico Linux com modelos Ollama locais. "
        "Funciona offline, em máquinas com 4GB RAM."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
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

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
# Após o mount de /static (linha ~30)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ✨ ADICIONE ISTO: Monta /images para o frontend
IMAGES_DIR = os.path.join(STATIC_DIR, "images")
if os.path.exists(IMAGES_DIR):
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")


@app.get("/", tags=["Frontend"], include_in_schema=False)
def frontend():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
