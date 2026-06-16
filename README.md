# 🤖 ALDE — Assistente Linux de Diagnóstico e Execução

[![ALDE CI](https://github.com/Croncl/alde/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Croncl/alde/actions/workflows/ci-cd.yml)

Um assistente virtual agêntico especializado em infraestrutura Linux, diagnósticos e ecossistema Docker. Utiliza a arquitetura **Ollama** + **FastAPI**, operando de forma **100% offline e local** com automação unificada via **Docker Compose**.

## 📋 Tabela de Conteúdos
- [Sobre o Projeto](#sobre-o-projeto)
- [Características](#características)
- [Tecnologias](#tecnologias)
- [Arquitetura de Modelos](#arquitetura-de-modelos)
- [Pré-requisitos](#pré-requisitos)
- [Instalação Local (Desenvolvimento)](#instalação-local-desenvolvimento)
- [Inicialização Unificada (Produção/Docker)](#inicialização-unificada-produção-docker)
- [Configuração (.env)](#configuração-env)
- [Uso e Exemplos](#uso-e-exemplos)
- [Frontend Web](#frontend-web)
- [Perfis de Usuário](#perfis-de-usuário)
- [Endpoints da API](#endpoints-da-api)
- [Recuperação de Contexto (KB Retrieval)](#recuperação-de-contexto-kb-retrieval)
- [Sessões em Memória](#sessões-em-memória)
- [CI/CD](#cicd)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Licença](#licença)

---

## 🎯 Sobre o Projeto

O **ALDE** é um engenheiro DevOps sênior virtual focado em resolução de problemas, análise forense de logs e orquestração de containers. Roda inteiramente na sua máquina e expõe uma **API RESTful** desenvolvida em FastAPI, além de um **frontend web** integrado acessível pelo navegador.

### Características

- ✅ **Frontend Web Integrado** — Interface de chat moderna servida diretamente pela API em `http://localhost:8000`, com temas claro/escuro, perfis de usuário e atalhos de diagnóstico.
- ✅ **Perfis de Especialidade** — Quatro modos de operação (Padrão, Infra e Redes, Suporte Técnico, DevOps) que ajustam tom, profundidade e temperatura do modelo.
- ✅ **Recuperação de Contexto (KB Retrieval)** — Injeção automática de comandos relevantes da `knowledge_base.json` em cada requisição, sem embeddings nem banco vetorial.
- ✅ **Janela de Contexto Massiva** — Suporte nativo a até **32k tokens** no modelo padrão, ideal para analisar logs extensos (`journalctl`, `dmesg`).
- ✅ **Inicialização em um Único Comando** — O ecossistema orquestra motor de IA, setup do modelo customizado e API automaticamente via Docker Compose.
- ✅ **Offline e Seguro** — Tráfego de dados estritamente local; API roda sob usuário não-root (`alde`) dentro do container.
- ✅ **Endpoints Especializados** — Rotas dedicadas para análise forense de logs, diagnóstico Docker/Compose e diagnóstico de hardware/drivers.

---

## 🛠️ Tecnologias

| Tecnologia | Versão | Finalidade |
|---|---|---|
| **Python** | 3.11 | Linguagem principal (⚠️ *Requisito estrito*: versões superiores como 3.13 exigem compilação manual do venv devido a travas do `pydantic-core` em Rust via PyO3) |
| **FastAPI** | 0.111.0 | Framework web assíncrono e documentação OpenAPI |
| **Ollama** | 0.6.2 | Gerenciador e runtime de LLMs locais |
| **qwen2.5-coder:1.5b** | — | Modelo padrão leve (4 GB RAM) |
| **qwen3-coder-next** | MoE | Modelo opcional pesado (16 GB RAM) |
| **Docker / Compose** | 24+ / 3.8+ | Containerização e orquestração do ecossistema |
| **Uvicorn** | 0.30.1 | Servidor ASGI de produção |
| **Pytest** | 8.2.2 | Testes unitários e de integração |
| **Ruff** | 0.4.9 | Linter e formatador estático |
| **Mypy** | 1.10.0 | Checagem estática de tipos |

---

## 🧠 Arquitetura de Modelos

O ALDE adota uma hierarquia dinâmica de fallback configurada em runtime, adaptando-se à disponibilidade do hardware local:

1. **`alde`** — Modelo customizado gerado automaticamente via `Modelfile` (persona e parâmetros otimizados).
2. **`qwen2.5-coder:1.5b`** — Modelo leve, baixado automaticamente na primeira execução. Requer 4 GB de RAM.
3. **`qwen3-coder-next`** — Arquitetura MoE opcional, 3B parâmetros ativos por token. Requer 16 GB de RAM.

A resolução do modelo acontece em runtime: o serviço percorre essa lista e usa o primeiro disponível no Ollama local.

---

## 📦 Pré-requisitos

- Sistema Operacional Linux (Debian 11+ ou Ubuntu 22.04+ recomendado).
- Arquitetura **x86_64**.
- Memória RAM mínima de **4 GB** para o modelo padrão (`qwen2.5-coder:1.5b`); **16 GB** para o modelo MoE opcional (`qwen3-coder-next`).
- Docker Engine instalado e daemon do Docker ativo.

---

## 🚀 Instalação Local (Desenvolvimento)

Para rodar os componentes isoladamente para depuração:

### 1. Preparar o Ambiente Python 3.11

Em sistemas cujo Python nativo seja divergente (ex: Debian 13 com Python 3.13):

```bash
sudo apt update && sudo apt install -y build-essential zlib1g-dev libncurses5-dev \
  libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xvf Python-3.11.9.tgz && cd Python-3.11.9
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall
```

### 2. Configurar o Ambiente Virtual

```bash
cd /caminho/do/projeto
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt
```

### 3. Configurar variáveis de ambiente

```bash
cp .env.example .env
# Edite OLLAMA_BASE_URL=http://localhost:11434 para desenvolvimento local
```

### 4. Rodar a API com reload automático

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🐳 Inicialização Unificada (Produção / Docker)

O projeto está totalmente automatizado. Não é necessário baixar modelos ou configurar o Ollama manualmente. O Docker Compose gerencia o ciclo completo:

```bash
docker compose up -d
```

Isso sobe três serviços em sequência:

1. **`alde-ollama`** — Motor de IA (Ollama).
2. **`alde-ollama-setup`** — Baixa `qwen2.5-coder:1.5b` e cria o modelo customizado `alde` via Modelfile. Roda uma única vez.
3. **`alde-api-service`** — API FastAPI com frontend web integrado.

> ⏳ **Primeira execução:** o setup baixa o modelo base (~1 GB) e cria a persona customizada. Execuções subsequentes são instantâneas. A **primeira resposta do chat pode levar 30s–2min** enquanto o modelo carrega na RAM.

Para acompanhar o progresso do download:

```bash
docker logs -f alde-ollama-setup
```

Para usar o modelo maior opcional:

```bash
docker exec alde-ollama ollama pull qwen3-coder-next
```

---

## ⚙️ Configuração (.env)

Copie o template e ajuste conforme necessário:

```bash
cp .env.example .env
```

Principais variáveis:

```env
# Motor de IA
OLLAMA_BASE_URL=http://ollama:11434   # http://localhost:11434 para dev local
OLLAMA_PORT=11434
OLLAMA_MODEL=qwen2.5-coder:1.5b
DEFAULT_MODEL=alde
OLLAMA_KEEP_ALIVE=5m                  # -1 para manter sempre carregado

# API
PORT=8000
API_HOST=0.0.0.0
ENVIRONMENT=production
LOG_LEVEL=info

# KB Retrieval
RETRIEVAL_TOP_N=6                     # comandos injetados por query
RETRIEVAL_MIN_SCORE=2                 # score mínimo para inclusão

# Histórico de sessão
MAX_HISTORY_ENTRIES=40
MAX_HISTORY_CHARS=80000

# CORS
CORS_ORIGINS=*
```

---

## 💻 Uso e Exemplos

A documentação interativa OpenAPI fica disponível em `http://localhost:8000/api/docs` e o frontend em `http://localhost:8000`.

### Chat via curl

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "como listar as portas abertas no sistema?",
    "profile": "devops"
  }'
```

### Análise forense de log

```bash
curl -X POST http://localhost:8000/analyze/logs \
  -H "Content-Type: application/json" \
  -d '{
    "log_content": "<conteúdo do log aqui>",
    "context": "serviço nginx caindo após atualização do kernel 6.1",
    "profile": "debug"
  }'
```

### Diagnóstico Docker

```bash
curl -X POST http://localhost:8000/diagnose/docker \
  -H "Content-Type: application/json" \
  -d '{
    "problem_description": "container killed, exiting with code 137",
    "docker_logs": "<saída de docker logs>",
    "compose_content": "<conteúdo do docker-compose.yml>"
  }'
```

### Diagnóstico de hardware

```bash
curl -X POST http://localhost:8000/diagnose/hardware \
  -H "Content-Type: application/json" \
  -d '{
    "problem_description": "driver Wi-Fi não carrega após atualização",
    "hw_output": "<saída de lspci -k e dmesg>",
    "kernel_version": "6.1.0-21-amd64",
    "distro": "Debian GNU/Linux 12 (bookworm)"
  }'
```

### Monitoramento da API

```bash
# Status de saúde
curl http://localhost:8000/health

# Modelos disponíveis no Ollama local
curl http://localhost:8000/models

# Histórico de sessão
curl http://localhost:8000/history/{session_id}

# Limpar sessão
curl -X DELETE http://localhost:8000/history/{session_id}
```

---

## 🖥️ Frontend Web

O ALDE inclui uma interface web integrada servida diretamente pela API em `http://localhost:8000`.

**Funcionalidades:**

- Chat em tempo real com suporte a blocos de código com botão de cópia.
- Alternância entre temas claro e escuro.
- Quatro perfis de especialidade selecionáveis na barra lateral (ver [Perfis de Usuário](#perfis-de-usuário)).
- Botões de atalho dinâmicos por perfil com queries pré-configuradas.
- Indicador de status do Ollama em tempo real (polling a cada 30s).
- Gerenciamento de sessão com exibição do ID ativo.
- Suporte a Shift+Enter para nova linha e Enter para envio.

---

## 👤 Perfis de Usuário

O perfil é passado via campo `profile` na requisição (API) ou selecionado na barra lateral (frontend). Cada perfil ajusta o system prompt e a temperatura do modelo:

| Perfil | `profile` | Temperatura | Foco |
|---|---|---|---|
| Padrão | `padrao` | 0.2 | Respostas equilibradas e práticas |
| Infra e Redes | `infra` | 0.1 | Kernel, hardware, rede, logs de sistema |
| Suporte Técnico | `suporte` | 0.3 | Passo a passo didático para qualquer nível |
| DevOps e Automação | `devops` | 0.15 | Docker, CI/CD, shell scripts |

Os perfis antigos `iniciante`, `avancado` e `debug` são mantidos para compatibilidade retroativa.

---

## 📡 Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Frontend web (interface de chat) |
| `GET` | `/health` | Status da API e do Ollama (usado pelo healthcheck Docker) |
| `POST` | `/chat` | Chat geral com suporte a sessões e streaming SSE |
| `POST` | `/analyze/logs` | Análise forense estruturada de logs longos |
| `POST` | `/diagnose/docker` | Diagnóstico de problemas Docker/Compose |
| `POST` | `/diagnose/hardware` | Diagnóstico de hardware e drivers |
| `GET` | `/history/{session_id}` | Histórico de mensagens de uma sessão |
| `DELETE` | `/history/{session_id}` | Remove histórico de uma sessão |
| `GET` | `/models` | Modelos instalados e disponíveis no Ollama local |
| `GET` | `/api/docs` | Documentação interativa Swagger UI |
| `GET` | `/api/redoc` | Documentação ReDoc |

O endpoint `/chat` aceita o campo `"stream": true` para retorno como stream SSE.

---

## 🔍 Recuperação de Contexto (KB Retrieval)

O ALDE enriquece automaticamente cada mensagem com comandos relevantes da `knowledge_base.json`, sem banco vetorial nem embeddings.

**Como funciona:**

1. A query é tokenizada (tokens alfanuméricos ≥ 3 chars, lowercase, sem stopwords PT/EN).
2. Cada entrada do JSON recebe um score de sobreposição de tokens com `cmd + desc`. Matches no campo `cmd` valem 2 pontos; matches em `desc` valem 1.
3. As entradas com score ≥ 2 e maior pontuação (padrão: top 6) são injetadas no system prompt antes de chamar o modelo.
4. O JSON é carregado uma única vez na startup via `lru_cache`.

**Exemplo:** a query `"como ver portas abertas?"` injeta automaticamente no contexto:

```
Comandos relevantes da base de conhecimento:
  • `ss -tulpn` — Portas em escuta com processo responsável
  • `lsof -i :<PORT>` — Processo usando porta específica
  • ...
```

A base cobre comandos de filesystem, processos, rede, logs, hardware, kernel/drivers, performance, Docker, systemd e segurança.

---

## 💾 Sessões em Memória

O histórico de conversação é mantido em memória (`_session_store`). **Reiniciar a API apaga todo o histórico.** Para conversas com contexto persistente, passe o mesmo `session_id` em todas as requisições enquanto o processo estiver rodando.

Limites configuráveis via `.env`:

- `MAX_HISTORY_ENTRIES=40` — máximo de mensagens por sessão.
- `MAX_HISTORY_CHARS=80000` — máximo de caracteres totais por sessão.

---

## 🔄 CI/CD

Pipeline automatizada via **GitHub Actions** (`.github/workflows/ci-cd.yml`) com três jobs em sequência:

1. **`lint`** — Checagem estática de tipos (`mypy`) + linting e formatação (`ruff check` e `ruff format --check`).
2. **`test`** — Suíte completa com `pytest` e cobertura via `pytest-cov`.
3. **`docker-build`** — Build da imagem Docker com cache GHA (sem publicação em registry).

Gatilhos: push em `main`, `feat/**` e `fix/**`; pull requests para `main`.

---

## 📁 Estrutura do Projeto

```text
projeto_alde/
├── .github/
│   └── workflows/
│       └── ci-cd.yml              # Pipeline de CI/CD (lint → test → docker build)
├── app/
│   ├── main.py                    # Ponto de entrada FastAPI + mount do frontend estático
│   ├── models.py                  # Schemas Pydantic (ChatRequest, ChatResponse, perfis…)
│   ├── routes/
│   │   ├── chat.py                # /chat, /analyze/logs, /diagnose/docker, /diagnose/hardware, /history
│   │   ├── health.py              # /health
│   │   └── models.py              # /models
│   ├── services/
│   │   ├── chat_service.py        # Lógica de sessão, construção de prompts e KB retrieval
│   │   └── ollama_service.py      # Integração com a API do Ollama (generate, chat, stream)
│   ├── static/
│   │   ├── index.html             # Frontend web (tema claro/escuro, perfis, chat)
│   │   └── images/                # Assets do mascote ALDE
│   └── utils/
│       └── helpers.py             # Utilitários (session_id, truncate_history, timestamp)
├── knowledge_base/
│   ├── knowledge_base.json        # Base estática de comandos Linux/Docker/hardware
│   ├── retrieval.py               # Tokenização, scoring e injeção de contexto no prompt
│   └── prompts_config.py          # Modelos, parâmetros, templates e system prompts por perfil
├── tests/
│   ├── conftest.py
│   ├── test_api.py                # Testes de integração dos endpoints
│   ├── test_retrieval.py          # Testes unitários do KB retrieval
│   └── test_services.py          # Testes do chat_service e helpers
├── docker-compose.yml             # Orquestração: Ollama + setup + API
├── Dockerfile                     # Imagem da API (non-root, python:3.11-slim)
├── Modelfile                      # Persona e parâmetros do modelo customizado `alde`
├── Makefile                       # Atalhos: dev, test, lint, format, logs, down
├── pyproject.toml                 # Configuração de ruff, mypy e pytest
├── requirements.txt               # Dependências de produção
├── requirements-dev.txt           # Dependências de desenvolvimento e teste
└── .env.example                   # Template de configuração do ambiente
```

---

## 🧰 Makefile

Atalhos disponíveis:

```bash
make dev        # Sobe o stack completo (Docker)
make dev-local  # Roda a API localmente com reload
make test       # Executa os testes com cobertura
make lint       # Verifica ruff + mypy
make format     # Formata o código com ruff
make docker     # Build da imagem Docker
make logs       # Logs da API em tempo real
make down       # Derruba o stack Docker
```

---

## 📄 Licença

Este projeto está sob os termos da licença **MIT**. Consulte o arquivo `LICENSE` para mais detalhes.

---

**Desenvolvido para administração de sistemas moderna, robusta e 100% local.** 🐧

**Feito com ❤️ para a comunidade Linux** 🐧
