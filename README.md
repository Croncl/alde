
# 🤖 Assistente Técnico Inteligente para Linux Debian/Ubuntu (ALDE)

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
- ✅ **Inteligência Avançada (MoE)** – Equipado com modelo de Mistura de Especialistas focado nativamente em recuperação de falhas de execução e análise agêntica.
- ✅ **Janela de Contexto Massiva** – Capacidade nativa de processar até **256k tokens**, ideal para analisar logs extensos de sistemas (`journalctl`, `dmesg`).
- ✅ **Inicialização em um Único Comando** – O ecossistema orquestra o motor de IA, o setup do modelo customizado e a API automaticamente.
- ✅ **Offline e Seguro** – Tráfego de dados estritamente local; operação segura rodando sob usuário não-root (`alde`) dentro do container.

---

## 🛠️ Tecnologias

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Python** | 3.11 | Linguagem principal (⚠️ *Requisito estrito*: versões superiores como a 3.13 que acompanham distribuições como o Debian 13 exigem compilação manual do venv devido a travas de compilação do `pydantic-core` em Rust via PyO3). |
| **FastAPI** | 0.111.0 | Framework web assíncrono |
| **Ollama** | 0.6.2 | Gerenciador e runtime de LLMs locais |
| **Qwen3-Coder-Next** | MoE | Modelo principal focado em código e automação CLI |
| **Docker / Compose** | 24+ / 3.8+ | Containerização e orquestração do ecossistema |
| **Uvicorn** | 0.30.1 | Servidor ASGI de produção |
| **Pytest** | 8.2.2 | Framework de testes unitários e de integração |
| **Ruff** | 0.4.9 | Linter e formatador estático ultra-rápido |

---

## 🧠 Arquitetura de Modelos
O ALDE adota uma hierarquia dinâmica de execução (fallback) configurada em runtime, adaptando-se à disponibilidade do hardware local:

1. **`alde`** (Modelo customizado gerado automaticamente via `Modelfile`)
2. **`qwen3-coder-next`** (Prioritário: Arquitetura MoE, 3B parâmetros ativos por token. Fornece raciocínio profundo com consumo de processamento reduzido).
3. **`qwen2.5-coder:1.5b`** (Fallback de contingência ultra leve para cenários de extrema restrição de hardware).

---

## 📦 Pré-requisitos
- Sistema Operacional Linux (Debian 11+ ou Ubuntu 22.04+ recomendado).
- Arquitetura **x86_64** (Processadores Intel Core i5 de 3ª geração ou superiores).
- Memória RAM mínima de **16 GB** para comportar o modelo MoE e o ecossistema de containers de teste em paralelo.
- Docker Engine instalado e o daemon do Docker ativo.

---

## 🚀 Instalação Local (Desenvolvimento)

Se você deseja rodar os componentes de forma isolada em sua máquina para depuração:

### 1. Preparar o Ambiente Python 3.11 (Exemplo para sistemas com Python nativo divergente)
```bash
sudo apt update && sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
wget [https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz](https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz)
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
pip install -r requirements.dev.txt

```

### 3. Rodar a API manualmente em Modo Recarga (Reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```

---

## 🐳 Inicialização Unificada (Produção / Docker)

O projeto está totalmente automatizado. Você **não precisa** baixar modelos ou configurar o Ollama antes de iniciar. O Docker Compose gerencia o ciclo completo de orquestração.

Para subir o ecossistema completo (Ollama + Compilador do Modelo ALDE + API FastAPI), execute na raiz do projeto:

```bash
docker compose up -d

```

> ⏳ **Nota sobre a primeira execução:** O container de setup irá detectar a inicialização do Ollama, baixar os gigabytes necessários do modelo base `qwen3-coder-next` e criar a persona customizada `alde`. Esse processo é executado uma única vez; as inicializações subsequentes são instantâneas utilizando os volumes persistidos.

Para monitorar o progresso do download e compilação do modelo da IA:

```bash
docker logs -f alde-ollama-setup

```

---

## ⚙️ Configuração

O comportamento do sistema é controlado pelo arquivo `.env`. Copie o modelo padrão para uso:

```bash
cp .env.example .env

```

Configurações recomendadas no seu `.env`:

```env
OLLAMA_HOST=http://alde-ollama:11434
OLLAMA_MODEL=qwen3-coder-next
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE="ALDE - Assistente Linux de Diagnóstico"
API_VERSION="1.0.0"
SYSTEM_PROMPT="Você é o ALDE. Responda estritamente focado em comandos verificados e segurança em sistemas Linux."

```

---

## 💻 Uso e Exemplos

A documentação interativa OpenAPI do FastAPI fica disponível imediatamente em: `http://localhost:8000/docs`

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

# Limpar o histórico de turnos da sessão atual
curl -X DELETE http://localhost:8000/history

```

---

## 📡 Endpoints da API

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `GET` | `/` | Metadados do projeto e status do sistema |
| `GET` | `/health` | Verificação de integridade (usada pelo Healthcheck do Docker) |
| `POST` | `/chat` | Envio de prompts de diagnóstico ou requisições de código |
| `GET` | `/history` | Retorna o histórico de conversação em memória |
| `DELETE` | `/history` | Limpa a memória de contexto da sessão |
| `GET` | `/models` | Consulta as tags de modelos prontas no Ollama local |

---

## 🔄 CI/CD

O projeto conta com uma pipeline automatizada via **GitHub Actions** (`.github/workflows/ci-cd.yml`) encarregada de executar:

1. Checagem estática de tipos com o `mypy`.
2. Linting e formatação estrita de código com o `ruff`.
3. Execução da suíte de testes automatizados com o `pytest` coletando cobertura através do `pytest-cov`.
4. Build e publicação da imagem Docker em caso de sucesso.

Certifique-se de configurar os seguintes Secrets no seu repositório do GitHub:

* `DOCKER_USERNAME`
* `DOCKER_TOKEN`

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
│   ├── knowledge_base.json    # Dicionário estático de comandos de suporte
│   └── prompts_config.py      # Configuração de fallbacks e parâmetros matemáticos (num_ctx)
├── tests/                     # Arquivos de teste do Pytest
├── docker-compose.yml         # Orquestração do Ollama, Setup e API
├── Dockerfile                 # Construção da imagem leve e segura da API (non-root)
├── Modelfile                  # Definição e System Prompt da Persona ALDE no Ollama
├── requirements.txt           # Dependências de produção
└── requirements.dev.txt       # Dependências de desenvolvimento e teste

```

---

## 📄 Licença

Este projeto está sob os termos da licença **MIT**. Consulte o arquivo `LICENSE` para obter mais detalhes.

---

**Desenvolvido para administração de sistemas moderna, robusta e 100% local.** 🐧


---

**Feito com ❤️ para a comunidade Linux** 🐧



