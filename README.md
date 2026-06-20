
# 🤖 Assistente Técnico Inteligente para Linux Debian/Ubuntu (ALDE)

[![ALDE CI](https://github.com/Croncl/alde/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Croncl/alde/actions/workflows/ci-cd.yml)

Um assistente virtual agêntico especializado em infraestrutura Linux, diagnósticos e ecossistema Docker. Ele utiliza a arquitetura **Ollama** + **FastAPI**, operando de forma 100% offline e local com automação unificada via **Docker Compose**.

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
- [Endpoints da API](#endpoints-da-api)  
- [CI/CD](#cicd)  
- [Estrutura do Projeto](#estrutura-do-projeto)  
- [Licença](#licença)  

---

## 🎯 Sobre o Projeto
O **ALDE** (Assistente Linux de Diagnóstico e Execução) é um engenheiro DevOps sênior virtual focado em resolução de problemas, análise forense de logs e orquestração de containers. Ele roda localmente e expõe uma API RESTful robusta desenvolvida em **FastAPI**.

### Características
- ✅ **Modelo leve e eficiente** – Roda com `qwen2.5-coder:1.5b` (~1 GB) em qualquer máquina com 4 GB de RAM, sem GPU necessária.
- ✅ **Janela de Contexto de 32k tokens** – Suficiente para analisar logs extensos de sistemas (`journalctl`, `dmesg`, `syslog`) em uma única requisição.
- ✅ **Inicialização em um Único Comando** – O ecossistema orquestra o motor de IA, o setup do modelo customizado e a API automaticamente.
- ✅ **Offline e Seguro** – Tráfego de dados estritamente local; operação segura rodando sob usuário não-root (`alde`) dentro do container.

---

## 🛠️ Tecnologias

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Python** | 3.11 | Linguagem principal (⚠️ *Requisito estrito*: versões superiores como a 3.13 que acompanham distribuições como o Debian 13 exigem compilação manual do venv devido a travas de compilação do `pydantic-core` em Rust via PyO3). |
| **FastAPI** | 0.111.0 | Framework web assíncrono |
| **Ollama** | 0.6.2 | Gerenciador e runtime de LLMs locais |
| **qwen2.5-coder:1.5b** | 1.5B | Modelo padrão — leve, eficiente, roda com 4 GB RAM |
| **qwen3-coder-next** | MoE (opcional) | Modelo pesado para hardware com 16+ GB RAM |
| **Docker / Compose** | 24+ / 3.8+ | Containerização e orquestração do ecossistema |
| **Uvicorn** | 0.30.1 | Servidor ASGI de produção |
| **Pytest** | 8.2.2 | Framework de testes unitários e de integração |
| **Ruff** | 0.4.9 | Linter e formatador estático ultra-rápido |

---

## 🧠 Arquitetura de Modelos
O ALDE adota uma hierarquia dinâmica de execução (fallback) configurada em runtime, adaptando-se à disponibilidade do hardware local:

1. **`alde`** — modelo customizado criado automaticamente via `Modelfile` (persona + parâmetros ajustados).
2. **`qwen2.5-coder:1.5b`** — modelo base leve; fallback imediato se `alde` ainda não foi criado.
3. **`qwen3-coder-next`** — modelo MoE pesado, opcional; só usado se disponível e com hardware suficiente.

---

## 📦 Pré-requisitos
- Sistema Operacional Linux (Debian 11+ ou Ubuntu 22.04+ recomendado).
- Arquitetura **x86_64** (Processadores Intel Core i5 de 3ª geração ou superiores).
- Memória RAM mínima de **4 GB** para o modelo padrão (`qwen2.5-coder:1.5b`). 16 GB para usar o modelo MoE opcional (`qwen3-coder-next`).
- Docker Engine instalado e o daemon do Docker ativo.

---

## 🚀 Instalação Local (Desenvolvimento)

Se você deseja rodar os componentes de forma isolada em sua máquina para depuração:

### 1. Preparar o Ambiente Python 3.11 (Exemplo para sistemas com Python nativo divergente)
```bash
sudo apt update && sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xvf Python-3.11.9.tgz && cd Python-3.11.9
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall

```

### 2. Configurar o Ambiente Virtual e Dependências de Desenvolvimento

```bash
cd /caminho/do/seu/projeto_alde
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements-dev.txt

```

### 3. Rodar a API manualmente em Modo Recarga (Reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```

---

## 🐳 Inicialização Unificada (Docker Compose)

O projeto está totalmente automatizado. Você **não precisa** baixar modelos ou configurar o Ollama antes de iniciar. O Docker Compose gerencia o ciclo completo de orquestração.

Para subir o ecossistema completo (Ollama + Compilador do Modelo ALDE + API FastAPI), execute na raiz do projeto:

```bash
docker compose up -d

```

> ⏳ **Nota sobre a primeira execução:** O container de setup irá baixar o modelo base `qwen2.5-coder:1.5b` (~1 GB) e criar a persona customizada `alde`. Esse processo é executado uma única vez; as inicializações subsequentes são instantâneas. A **primeira resposta do chat demora 30s–2min** enquanto o modelo carrega na RAM — depois fica instantâneo.

> 💻 **Requisitos de hardware:** 4 GB de RAM disponíveis é suficiente para o modelo padrão (`qwen2.5-coder:1.5b`). Para usar o modelo maior opcional (`qwen3-coder-next`), são necessários 16 GB.

Para monitorar o progresso do download e compilação do modelo da IA:

```bash
docker logs -f alde-ollama-setup

```

Quando o setup concluir, o projeto está pronto:

| Interface | URL |
|-----------|-----|
| **Chat (aplicação)** | `http://localhost:8000` |
| **API Docs (Swagger)** | `http://localhost:8000/api/docs` |
| **Health check** | `http://localhost:8000/health` |

---

## ⚙️ Configuração

O comportamento do sistema é controlado pelo arquivo `.env`. Copie o modelo padrão para uso:

```bash
cp .env.example .env

```

Variáveis disponíveis no `.env`:

```env
# URL do Ollama — não altere ao usar Docker Compose (já definida pelo compose)
OLLAMA_BASE_URL=http://localhost:11434

# Porta da API (padrão: 8000). Mude se houver conflito com outro serviço.
PORT=8000
```

> **Modelo grande (opcional):** após o `docker compose up -d`, execute manualmente se quiser o modelo mais pesado:
> ```bash
> docker exec alde-ollama ollama pull qwen3-coder-next
> ```

---

## 💻 Uso e Exemplos

A documentação interativa OpenAPI do FastAPI fica disponível imediatamente em: `http://localhost:8000/api/docs`

### Exemplo de Diagnóstico de Logs via Terminal (`curl`)

O ALDE aceita strings extensas de logs para análise de causa-raiz:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analise o seguinte erro do docker-compose: container killed, exiting with code 137",
    "profile": "debug"
  }'

```

### Comandos de Monitoramento Úteis

```bash
# Verificar status de saúde da API
curl http://localhost:8000/health

# Listar os modelos carregados e disponíveis no motor local
curl http://localhost:8000/models

# Limpar o histórico de uma sessão
curl -X DELETE http://localhost:8000/history/{session_id}

```

---

## 📡 Endpoints da API

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/` | Metadados do projeto e status do sistema |
| `GET` | `/health` | Verificação de integridade (Ollama online + modelo carregado) |
| `POST` | `/chat` | Chat com o assistente ALDE |
| `POST` | `/analyze/logs` | Análise forense de logs longos |
| `POST` | `/diagnose/docker` | Diagnóstico de problemas Docker/Compose |
| `POST` | `/diagnose/hardware` | Diagnóstico de hardware e drivers |
| `GET` | `/history/{session_id}` | Retorna o histórico de conversação da sessão |
| `DELETE` | `/history/{session_id}` | Limpa o histórico da sessão |
| `GET` | `/models` | Consulta os modelos disponíveis no Ollama local |

---

## 🔍 Recuperação de Contexto (KB Retrieval)

O ALDE enriquece automaticamente cada mensagem com comandos relevantes da `knowledge_base.json`, sem banco vetorial nem embeddings.

**Como funciona:**
1. A query é tokenizada (tokens alfanuméricos ≥ 3 chars, lowercase).
2. Cada entrada do JSON recebe um score de sobreposição de tokens com `cmd + desc`.
3. As 6 entradas com maior score são injetadas no system prompt antes de chamar o modelo.
4. O JSON é carregado uma única vez na startup via `lru_cache`.

**Exemplo:** `"como listar arquivos grandes?"` injeta automaticamente no contexto:
```
Comandos relevantes da base de conhecimento:
  • `ls -lah --color=auto` — Lista arquivos com tamanho legível e permissões
  • `find /path -name '*.log' -mtime -7 -size +10M` — Localiza logs recentes maiores que 10MB
  • ...
```

---

## 💾 Sessões em Memória

O histórico de conversação fica em memória (`_session_store`). **Reiniciar a API apaga todo o histórico.** Para conversas com contexto, passe sempre o mesmo `session_id` nos requests enquanto o processo estiver rodando.

---

## 🔄 CI/CD

O projeto conta com uma pipeline automatizada via **GitHub Actions** (`.github/workflows/ci-cd.yml`) com 3 jobs:

1. **lint** — `ruff check` + `ruff format --check` + `mypy app/`.
2. **test** — 23 testes com `pytest` (mocks isolam o Ollama — roda sem LLM instalado).
3. **docker-build** — Build da imagem com `docker/build-push-action` e cache GHA (sem publicação em registry).

---

## 📁 Estrutura do Projeto

```text
projeto_alde/
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # Pipeline de integração contínua
├── app/
│   ├── main.py                # Ponto de entrada FastAPI e Uvicorn
│   ├── models.py              # Esquemas de dados Pydantic
│   ├── routes/                # Endpoints RESTful da aplicação
│   └── services/              # Integração direta com a API do Ollama
├── knowledge_base/
│   ├── knowledge_base.json    # Dicionário estático de comandos Linux/Docker/hardware
│   ├── retrieval.py           # Busca por keyword e injeção de contexto no prompt
│   └── prompts_config.py      # Configuração de fallbacks e parâmetros do modelo
├── tests/                     # Arquivos de teste do Pytest
├── docker-compose.yml         # Orquestração do Ollama, Setup e API
├── Dockerfile                 # Construção da imagem leve e segura da API (non-root)
├── Modelfile                  # Definição e System Prompt da Persona ALDE no Ollama
├── requirements.txt           # Dependências de produção
└── requirements-dev.txt       # Dependências de desenvolvimento e teste

```

---

## 🎓 Contexto Acadêmico

Projeto desenvolvido como trabalho prático para a disciplina **IMD0035 — MLOps** da Universidade Federal do Rio Grande do Norte (UFRN) / Instituto Metrópole Digital.

- **Professor:** Adelson de Araujo
- **Alunos:** Cristovão Lacerda Cronje · João Gilberto Neves Saraiva

---

## 📄 Licença

Este projeto está sob os termos da licença **MIT**. Consulte o arquivo `LICENSE` para obter mais detalhes.

---

**Desenvolvido para administração de sistemas moderna, robusta e 100% local.** 🐧


---

**Feito com ❤️ para a comunidade Linux** 🐧



