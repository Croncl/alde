# 🤖 Assistente Técnico Inteligente para Linux

Um assistente virtual especializado em comandos e ferramentas Linux, utilizando **Ollama** + **FastAPI** com CI/CD automatizado via GitHub Actions e Docker.

## 📋 Tabela de Conteúdos

- [Sobre o Projeto](#sobre-o-projeto)
- [Tecnologias](#tecnologias)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Endpoints da API](#endpoints-da-api)
- [Docker](#docker)
- [CI/CD](#cicd)
- [Personalização](#personalização)
- [Contribuição](#contribuição)
- [Licença](#licença)

## 🎯 Sobre o Projeto

Este projeto oferece um **assistente técnico inteligente** especializado em ajudar usuários com comandos e ferramentas Linux. Utilizando modelos de linguagem via Ollama e uma API robusta com FastAPI, o assistente é leve, fácil de implantar e pode ser executado em qualquer máquina Linux (Debian/Ubuntu).

### Características principais

- ✅ **Leve e eficiente** - Baixo consumo de recursos
- ✅ **Containerizado** - Docker para fácil implantação
- ✅ **CI/CD automatizado** - GitHub Actions para build, testes e linting
- ✅ **Configurável** - Personalize prompts e modelos
- ✅ **API RESTful** - Endpoints simples e documentados
- ✅ **Respostas técnicas** - Especializado em Linux

## 🛠️ Tecnologias

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Python** | 3.11+ | Linguagem principal |
| **FastAPI** | 0.100+ | Framework web |
| **Ollama** | 0.1+ | Modelos LLM locais |
| **Docker** | 24+ | Containerização |
| **GitHub Actions** | - | CI/CD Pipeline |
| **Pytest** | 7+ | Testes |
| **Ruff** | 0.1+ | Linter/Formatter |
| **Uvicorn** | 0.23+ | Servidor ASGI |

## 📦 Pré-requisitos

### Sistema Operacional
- Linux (Debian/Ubuntu recomendado)
- Ou qualquer sistema com Docker

### Dependências
```bash
# Para instalação local
Python 3.11 ou superior
Ollama instalado e rodando

# Para Docker
Docker Engine 24+
Docker Compose (opcional)
```

## 🚀 Instalação

### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/assistente-linux-ai.git
cd assistente-linux-ai
```

### 2. Instalar dependências
```bash
# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Instalar pacotes
pip install -r requirements.txt
```

### 3. Instalar e configurar Ollama
```bash
# Instalar Ollama (Linux)
curl -fsSL https://ollama.com/install.sh | sh

# Baixar modelo recomendado
ollama pull llama3.2:3b  # Leve e eficiente
# ou
ollama pull mistral:7b   # Mais robusto
```

### 4. Iniciar o servidor
```bash
# Modo desenvolvimento
uvicorn app.main:app --reload

# Modo produção
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## ⚙️ Configuração

### Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# API
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE="Assistente Linux AI"
API_VERSION="1.0.0"

# Contexto
MAX_HISTORY=10
SYSTEM_PROMPT="Você é um especialista em Linux. Ajude com comandos e ferramentas."
```

### Configuração do modelo

O assistente usa prompts especializados:

```python
SYSTEM_PROMPT = """
Você é um assistente técnico especializado em Linux.
- Forneça comandos práticos e exemplos
- Explique ferramentas comuns (grep, awk, sed, etc)
- Mantenha respostas concisas e úteis
- Inclua flags importantes quando necessário
"""
```

## 💻 Uso

### Interface Web (Swagger UI)

Acesse `http://localhost:8000/docs` para documentação interativa.

### Exemplos de uso

#### Chat simples
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Como listar todos os arquivos .log em uma pasta?"
  }'
```

**Resposta esperada:**
```json
{
  "response": "Use: find /caminho -name \"*.log\" -type f\n\nPara listar recursivamente: ls -R | grep \\.log$\n\nCom detalhes: find . -name \"*.log\" -ls",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Conversa com histórico
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "E como buscar um texto específico dentro desses logs?",
    "session_id": "usuario123"
  }'
```

### Comandos úteis para testar

```bash
# Verificar status da API
curl http://localhost:8000/health

# Ver modelos disponíveis no Ollama
curl http://localhost:11434/api/tags

# Teste rápido no terminal
python -c "import requests; print(requests.post('http://localhost:8000/chat', json={'message':'comando para ver processos'}).json())"
```

## 📡 Endpoints da API

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Informações do projeto |
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Enviar mensagem |
| `GET` | `/history/{session_id}` | Obter histórico |
| `DELETE` | `/history/{session_id}` | Limpar histórico |
| `GET` | `/models` | Listar modelos disponíveis |

### Detalhes dos endpoints

#### `POST /chat`
```json
{
  "message": "string (obrigatório)",
  "session_id": "string (opcional)",
  "temperature": 0.7,
  "max_tokens": 500
}
```

**Resposta:**
```json
{
  "response": "string",
  "model": "llama3.2:3b",
  "timestamp": "ISO 8601",
  "session_id": "string"
}
```

## 🐳 Docker

### Build da imagem
```bash
# Build local
docker build -t assistente-linux-ai:latest .

# Build com tag específica
docker build -t assistente-linux-ai:v1.0.0 .
```

### Executar com Docker

#### Opção 1: Docker run
```bash
docker run -d \
  --name assistente-linux \
  -p 8000:8000 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  assistente-linux-ai:latest
```

#### Opção 2: Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    ports:
      - "11434:11434"
  
  assistente:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
    volumes:
      - ./logs:/app/logs

volumes:
  ollama_data:
```

```bash
# Executar com Compose
docker-compose up -d

# Ver logs
docker-compose logs -f assistente
```

### Dockerfile exemplo
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar usuário não-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expor porta
EXPOSE 8000

# Comando para iniciar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔄 CI/CD (GitHub Actions)

### Workflow completo

Crie `.github/workflows/ci-cd.yml`:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      - name: Linting (Ruff)
        run: |
          ruff check .
          ruff format --check .
      
      - name: Run tests
        run: |
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/assistente-linux:latest
            ${{ secrets.DOCKER_USERNAME }}/assistente-linux:${{ github.sha }}
```

### Secrets necessários

No repositório GitHub, adicione:
- `DOCKER_USERNAME` - Usuário Docker Hub
- `DOCKER_TOKEN` - Token de acesso Docker Hub

## 🎨 Personalização

### Adicionar conhecimento específico

Crie um arquivo `knowledge_base.json`:

```json
{
  "comandos": {
    "find": "Busca arquivos...",
    "grep": "Busca texto...",
    "awk": "Processamento de texto..."
  },
  "ferramentas": {
    "docker": "Containerização...",
    "git": "Controle de versão..."
  }
}
```

### Customizar prompt do sistema

```python
# app/config.py
CUSTOM_PROMPTS = {
    "iniciante": "Explique comandos básicos de forma simples...",
    "avancado": "Foque em otimização e boas práticas...",
    "debug": "Ajude a diagnosticar problemas de sistema..."
}
```

## 📁 Estrutura do Projeto

```
assistente-linux-ai/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   │   ├── chat.py
│   │   └── health.py
│   ├── services/
│   │   ├── ollama_service.py
│   │   └── chat_service.py
│   └── utils/
│       └── helpers.py
├── tests/
│   ├── test_api.py
│   └── test_services.py
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements-dev.txt
└── requirements.txt
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

### Padrões de código
- Use **Ruff** para linting e formatação
- Escreva testes para novas funcionalidades
- Mantenha a documentação atualizada

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Suporte

- 📧 Email:  
- 🐛 Issues: [GitHub Issues](link)
- 💬 Discussões: [GitHub Discussions](link)

---

**Feito com ❤️ para a comunidade Linux** 🐧