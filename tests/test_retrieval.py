from unittest.mock import patch

from knowledge_base.retrieval import _tokenize, retrieve

_FAKE_ENTRIES = [
    {"cmd": "ls -lah", "desc": "Lista arquivos com permissões", "category": "linux.filesystem"},
    {
        "cmd": "df -hT",
        "desc": "Espaço em disco por sistema de arquivos",
        "category": "linux.filesystem",
    },
    {"cmd": "docker ps", "desc": "Lista containers em execução", "category": "docker.containers"},
]


def _with_fake_kb(fn):
    """Decorator: substitui _load_entries pelo conjunto controlado."""
    with patch("knowledge_base.retrieval._load_entries", return_value=_FAKE_ENTRIES):
        fn()


def test_retrieve_empty_query_returns_empty():
    assert retrieve("") == ""
    assert retrieve("   ") == ""


def test_retrieve_no_match_returns_empty():
    with patch("knowledge_base.retrieval._load_entries", return_value=_FAKE_ENTRIES):
        result = retrieve("quantum entanglement supernova")
    assert result == ""


def test_retrieve_keyword_match_returns_block():
    with patch("knowledge_base.retrieval._load_entries", return_value=_FAKE_ENTRIES):
        # ✨ Query com palavras que aparecem na descrição para gerar score >= 2
        result = retrieve("lista arquivos permissões")
    assert result.startswith("Comandos relevantes da base de conhecimento:")
    assert "ls -lah" in result


def test_retrieve_docker_keyword_matches_docker_entry():
    with patch("knowledge_base.retrieval._load_entries", return_value=_FAKE_ENTRIES):
        result = retrieve("docker containers execução")
    assert "docker ps" in result


def test_retrieve_respects_top_n():
    with patch("knowledge_base.retrieval._load_entries", return_value=_FAKE_ENTRIES):
        result = retrieve("lista arquivos containers disco", top_n=1)
    lines = [line for line in result.splitlines() if line.strip().startswith("•")]
    assert len(lines) == 1


def test_tokenize_strips_short_tokens():
    tokens = _tokenize("ls -la /etc")
    assert "ls" not in tokens  # len < 3
    assert "etc" in tokens


def test_tokenize_lowercases():
    tokens = _tokenize("ListaArquivos DISCO")
    assert all(t == t.lower() for t in tokens)
