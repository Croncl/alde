# knowledge_base/prompts_config.py
"""
Configuração centralizada de prompts e parâmetros de geração do ALDE.
Ajustado para uso com qwen2.5-coder:1.5b (modelo leve).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Hierarquia de fallback de modelos
# ---------------------------------------------------------------------------
MODEL_PREFERENCE: list[str] = [
    "alde",  # modelo customizado via `ollama create alde -f Modelfile`
    "qwen2.5-coder:1.5b",  # modelo leve — prioridade quando recursos são limitados
    "qwen3-coder-next",  # MoE pesado, só se disponível
]

DEFAULT_MODEL: str = MODEL_PREFERENCE[0]

# ---------------------------------------------------------------------------
# Parâmetros de geração ajustados para 1.5B
# ---------------------------------------------------------------------------
GENERATION_PARAMS: dict = {
    "temperature": 0.2,
    "top_p": 0.85,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "num_ctx": 32768,
    "num_predict": -1,
    "stop": ["<|im_end|>", "<|endoftext|>"],
}

# Parâmetros sobrescritos por perfil de usuário
PROFILE_OVERRIDES: dict[str, dict] = {
    "padrao": {"temperature": 0.2},
    "infra": {"temperature": 0.1},
    "suporte": {"temperature": 0.3},
    "devops": {"temperature": 0.15},
    # Mantém compatibilidade com nomes antigos
    "iniciante": {"temperature": 0.3},
    "avancado": {"temperature": 0.1},
    "debug": {"temperature": 0.0},
}

# ---------------------------------------------------------------------------
# System prompt base de sessão
# ---------------------------------------------------------------------------
SESSION_SYSTEM_PREFIX: str = (
    "Você é o ALDE, assistente especialista em Linux, Docker e infraestrutura. "
    "Responda SEMPRE em português do Brasil. "
    "Blocos de código, comandos e nomes técnicos permanecem em inglês/ASCII. "
    "Seja direto e objetivo — forneça comandos prontos para uso."
)

# ---------------------------------------------------------------------------
# ✨ NOVO: System prompts específicos por perfil
# ---------------------------------------------------------------------------
PROFILE_SYSTEM_PROMPTS: dict[str, str] = {
    "padrao": (
        "Você é o ALDE no modo Padrão. "
        "Forneça respostas equilibradas, claras e práticas. "
        "Use os comandos da base de conhecimento quando relevantes."
    ),
    "infra": (
        "Você é o ALDE no modo Infraestrutura e Redes. "
        "Especialize-se em diagnóstico de kernel, hardware, interfaces de rede, "
        "roteamento, DNS, firewall e logs de sistema. "
        "Priorize comandos de baixo nível (ip, ss, dmesg, journalctl, lspci, lsmod). "
        "Use os comandos da base de conhecimento como referência prioritária."
    ),
    "suporte": (
        "Você é o ALDE no modo Suporte Técnico. "
        "Forneça respostas didáticas com passo a passo claro para qualquer nível de usuário. "
        "Explique o que cada comando faz antes de executá-lo. "
        "Use linguagem acessível e evite jargões excessivos. "
        "Use os comandos da base de conhecimento como referência."
    ),
    "devops": (
        "Você é o ALDE no modo DevOps e Automação. "
        "Especialize-se em Docker, docker-compose, shell scripts, CI/CD e boas práticas. "
        "Priorize comandos idempotentes, seguros e com tratamento de erros. "
        "Use os comandos da base de conhecimento como referência prioritária."
    ),
}

# ---------------------------------------------------------------------------
# Templates de diagnóstico
# ---------------------------------------------------------------------------
DIAGNOSTIC_PROMPT_TEMPLATE: str = """Analise o log/erro abaixo e responda com:

1. **Causa-raiz** — linha ou timestamp do primeiro erro
2. **Processo/serviço** — nome e PID (se visível)
3. **Sequência de eventos** — como o erro se propagou
4. **Comandos de verificação** — para confirmar o diagnóstico
5. **Solução** — passo a passo com comandos prontos
6. **Prevenção** — como evitar recorrência

Perfil: {profile}
Contexto: {context}

--- LOG ---
{log_content}
--- FIM ---
"""

DOCKER_DIAGNOSE_TEMPLATE: str = """Analise o problema Docker/Compose abaixo e forneça diagnóstico com comandos de verificação e solução.

Problema: {problem}

Saída docker inspect/logs:
{docker_output}

docker-compose.yml:
{compose_content}
"""

HARDWARE_DIAGNOSE_TEMPLATE: str = """Diagnostique o problema de hardware/driver abaixo em sistema Debian/Ubuntu.

Problema: {problem}

Saída dos comandos de diagnóstico:
{hw_output}

Kernel: {kernel_version}
Distribuição: {distro}
"""

# ---------------------------------------------------------------------------
# Comandos de coleta de contexto sugeridos ao usuário
# ---------------------------------------------------------------------------
CONTEXT_COLLECTION_COMMANDS: dict[str, list[str]] = {
    "hardware_geral": [
        "inxi -Fxz 2>/dev/null || lshw -short 2>/dev/null",
        "uname -a",
        "lsb_release -a 2>/dev/null || cat /etc/os-release",
    ],
    "logs_sistema": [
        "journalctl -b --no-pager -p err..emerg | tail -200",
        "dmesg -T --level=err,crit,alert,emerg | tail -100",
    ],
    "rede": [
        "ip -br addr",
        "ip route show",
        "ss -tulpn",
        "resolvectl status 2>/dev/null || cat /etc/resolv.conf",
    ],
    "docker": [
        "docker version --format '{{.Server.Version}}'",
        "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
        "docker system df",
        "docker network ls",
    ],
    "storage": [
        "df -hT",
        "lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT",
        "cat /etc/fstab | grep -v '^#'",
    ],
    "processos": [
        "ps auxf --sort=-%mem | head -30",
        "free -h",
        "uptime",
    ],
}