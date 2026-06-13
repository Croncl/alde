.PHONY: dev test lint format docker docker-down logs help

help:
	@echo "Comandos disponíveis:"
	@echo "  make dev       - Sobe o stack completo (Docker)"
	@echo "  make dev-local - Roda a API localmente com reload"
	@echo "  make test      - Executa os testes"
	@echo "  make lint      - Verifica lint e tipos"
	@echo "  make format    - Formata o código"
	@echo "  make docker    - Build da imagem Docker"
	@echo "  make logs      - Logs da API em tempo real"
	@echo "  make down      - Derruba o stack Docker"

dev:
	docker compose up -d
	@echo "API em: http://localhost:8000"
	@echo "Docs:   http://localhost:8000/api/docs"

dev-local:
	. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	. .venv/bin/activate && pytest

lint:
	. .venv/bin/activate && ruff check . && ruff format --check . && mypy app/

format:
	. .venv/bin/activate && ruff format .

docker:
	docker build -t alde-api .

logs:
	docker logs -f alde-api-service

down:
	docker compose down
