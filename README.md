---

# 🤖 Assistente Técnico Inteligente para Linux Debian (ALDE)

Um assistente virtual especializado em comandos e ferramentas Linux, utilizando **Ollama** + **FastAPI**, com CI/CD automatizado via GitHub Actions e Docker.

## 📋 Tabela de Conteúdos
- [Sobre o Projeto](#sobre-o-projeto)  
- [Características](#características)  
- [Tecnologias](#tecnologias)  
- [Pré-requisitos](#pré-requisitos)  
- [Instalação](#instalação)  
- [Configuração](#configuração)  
- [Uso](#uso)  
- [Endpoints da API](#endpoints-da-api)  
- [Docker](#docker)  
- [CI/CD](#cicd)  
- [Personalização](#personalização)  
- [Estrutura do Projeto](#estrutura-do-projeto)  
- [Contribuição](#contribuição)  
- [Licença](#licença)  

---

## 🎯 Sobre o Projeto
O **ALDE** é um assistente técnico inteligente para Linux, rodando localmente com **Ollama** e exposto via **FastAPI**.  
Ele responde perguntas sobre terminal, rede, processos, Docker, Git e muito mais — sem depender de internet ou cloud.

### Características
- ✅ **Leve e eficiente** – funciona até em máquinas com 4GB RAM  
- ✅ **Containerizado** – fácil implantação com Docker  
- ✅ **CI/CD automatizado** – pipeline com GitHub Actions  
- ✅ **Configurável** – prompts e perfis customizáveis  
- ✅ **API RESTful** – endpoints simples e documentados  
- ✅ **Offline** – não depende de serviços externos  

---

## 🛠️ Tecnologias

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Python** | 3.11 | Linguagem principal (⚠️ necessário usar **Python 3.11** porque o `pydantic-core`, dependência do FastAPI/Pydantic, ainda não suporta Python 3.13. Se usar 3.13, a instalação falha ao compilar o módulo em Rust via PyO3. No Debian 13, o Python padrão é 3.13, então é preciso compilar e instalar o Python 3.11 manualmente para criar o venv) |
| **FastAPI** | 0.100+ | Framework web |
| **Ollama** | 0.1+ | Modelos LLM locais |
| **Docker** | 24+ | Containerização |
| **GitHub Actions** | - | CI/CD Pipeline |
| **Pytest** | 7+ | Testes |
| **Ruff** | 0.1+ | Linter/Formatter |
| **Uvicorn** | 0.23+ | Servidor ASGI |

---

## 📦 Pré-requisitos
- Linux (Debian/Ubuntu recomendado)  
- **Python 3.11** (⚠️ no Debian 13 é necessário compilar manualmente, pois o repositório oficial só traz Python 3.13)  
- Ollama instalado e rodando  
- Docker Engine 24+ (opcional, para containerização)  

---

## 🚀 Instalação

### Instalar Python 3.11 no Debian 13
```bash
sudo apt update
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev \
    libnss3-dev libssl-dev libreadline-dev libffi-dev wget

wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xvf Python-3.11.9.tgz
cd Python-3.11.9
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall   # instala python3.11 sem substituir o python3 padrão
```

---

### 📦 Criar ambiente virtual e instalar dependências
```bash
cd ~/Documentos/Projetos/projeto_alde
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate

# Atualizar ferramentas básicas
pip install --upgrade pip setuptools wheel

# Instalar dependências do projeto
pip install -r requirements.txt
```

---

### 🚀 Instalar Ollama (binário do servidor)
```bash
# Instalar Ollama no sistema
curl -fsSL https://ollama.com/install.sh | sh
```

---

### 📥 Baixar modelo necessário
```bash
ollama pull llama3.2:3b
```

---

### 💻 Rodar a aplicação
```bash
uvicorn app.main:app --reload
```
---

## ⚙️ Configuração
Crie um arquivo `.env`:
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
API_HOST=0.0.0.0
API_PORT=8000
API_TITLE="Assistente Linux AI"
API_VERSION="1.0.0"
SYSTEM_PROMPT="Você é um especialista em Linux. Ajude com comandos e ferramentas."
```

Perfis disponíveis (em `prompts_config.py`):
- `default` → respostas técnicas diretas  
- `iniciante` → explicações simples com avisos  
- `avancado` → conciso, flags avançadas  
- `debug` → foco em diagnóstico  

---

## 💻 Uso
Acesse a documentação interativa: `http://localhost:8000/docs`

### Exemplos
```bash
# Chat simples
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "como listar arquivos por tamanho?"}'

# Histórico (em memória da execução atual)
curl http://localhost:8000/history

# Listar modelos instalados
curl http://localhost:8000/models

# Status da API
curl http://localhost:8000/health
```

---

## 📡 Endpoints da API
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/` | Informações do projeto |
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Enviar mensagem |
| `GET` | `/history` | Obter histórico atual |
| `DELETE` | `/history` | Limpar histórico |
| `GET` | `/models` | Listar modelos disponíveis |

---

## 🐳 Docker
### Build da imagem
```bash
docker build -t assistente-linux-ai:latest .
```

### Executar com Docker Compose
```bash
docker compose up -d
```

Na primeira execução, baixe o modelo:
```bash
docker exec alde-ollama ollama pull llama3.2:3b
```

---

## 🔄 CI/CD
Pipeline com testes, linting e build automático via GitHub Actions.  

Secrets necessários:  
- `DOCKER_USERNAME`  
- `DOCKER_TOKEN`  

---

## 📚 Base de Conhecimento

O ALDE utiliza como referência principal a documentação oficial do Debian:

- [Documentação Debian em Português](https://www.debian.org/doc/user-manuals.pt.html#faq)

Esses manuais fornecem respostas para dúvidas frequentes, guias de instalação e boas práticas de administração de sistemas Linux.

---


## 🎨 Personalização
Adicione conhecimento específico em `knowledge_base.json`:
```json
{
  "comandos": {
    "find": "Busca arquivos...",
    "grep": "Busca texto...",
    "awk": "Processamento de texto..."
  }
}
```

Perfis customizados em `prompts_config.py`:
```python
CUSTOM_PROMPTS = {
    "iniciante": "Explique comandos básicos de forma simples...",
    "avancado": "Foque em otimização e boas práticas...",
    "debug": "Ajude a diagnosticar problemas de sistema..."
}
```

---

## 📁 Estrutura do Projeto
```
assistente-linux-ai/
├── .github/workflows/ci-cd.yml
├── app/
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   ├── services/
│   └── utils/
├── knowledge_base/
│   ├── knowledge_base.json
│   └── prompts_config.py
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 🤝 Contribuição
1. Fork o projeto  
2. Crie uma branch (`git checkout -b feature/minha-feature`)  
3. Commit (`git commit -m 'feat: minha feature'`)  
4. Push (`git push origin feature/minha-feature`)  
5. Abra um Pull Request  

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---


## 📞 Suporte

- 📧 Email:  
- 🐛 Issues: [GitHub Issues](link)
- 💬 Discussões: [GitHub Discussions](link)

---

**Feito com ❤️ para a comunidade Linux** 🐧



