"""
Retrieval de comandos Linux relevantes a partir da knowledge_base.json.

Dado o texto de uma mensagem, extrai os N comandos mais relevantes por
sobreposição de keywords entre a query e os campos cmd/desc de cada entrada.
Usado para injetar contexto cirúrgico no prompt antes de chamar o modelo.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_KB_PATH = Path(__file__).parent / "knowledge_base.json"
_TOP_N = 6
_MIN_SCORE = 2  # Aumentado de 1 para 2 para reduzir ruído

# Stopwords em português e inglês que não agregam semântica
_STOPWORDS = {
    "com", "para", "como", "sem", "por", "uma", "das", "dos",
    "the", "and", "for", "with", "how", "what", "when", "where",
    "que", "qual", "quais", "ver", "usar", "fazer", "ser", "esta",
    "este", "isso", "esse", "aquilo", "sobre", "entre", "apos",
}


@lru_cache(maxsize=1)
def _load_entries() -> list[dict]:
    """Carrega e flatten o JSON em lista de entradas. Cached na startup."""
    if not _KB_PATH.exists():
        logger.error("knowledge_base.json não encontrado em %s", _KB_PATH)
        return []

    try:
        with _KB_PATH.open(encoding="utf-8") as f:
            kb = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Erro ao carregar knowledge_base.json: %s", e)
        return []

    entries = []
    for category, subcategories in kb.items():
        if category == "metadata":
            continue
        if not isinstance(subcategories, dict):
            continue
        for subcategory, items in subcategories.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict) and "cmd" in item:
                    entries.append(
                        {
                            "cmd": item["cmd"],
                            "desc": item.get("desc", ""),
                            "category": f"{category}.{subcategory}",
                        }
                    )

    logger.debug("Carregadas %d entradas da knowledge base", len(entries))
    return entries


def _tokenize(text: str) -> set[str]:
    """Extrai tokens alfanuméricos com 3+ caracteres, lowercase, sem stopwords."""
    tokens = {
        t
        for t in re.split(r"[^a-zA-ZÀ-ÿ0-9]+", text.lower())
        if len(t) >= 3 and t not in _STOPWORDS
    }
    return tokens


def _score(entry: dict, query_tokens: set[str]) -> int:
    """
    Conta sobreposição de tokens entre query e cmd+desc da entrada.
    Dá peso 2x para matches no campo cmd (nome do comando é mais relevante).
    """
    cmd_tokens = _tokenize(entry["cmd"])
    desc_tokens = _tokenize(entry["desc"])

    # Match no cmd vale 2 pontos, match na desc vale 1
    cmd_matches = len(query_tokens & cmd_tokens) * 2
    desc_matches = len(query_tokens & desc_tokens)

    return cmd_matches + desc_matches


def retrieve(query: str, top_n: int = _TOP_N) -> str:
    """
    Retorna bloco de texto com os comandos mais relevantes para a query.
    Retorna string vazia se nenhuma entrada atingir score mínimo.
    """
    if not query.strip():
        return ""

    query_tokens = _tokenize(query)
    if not query_tokens:
        return ""

    entries = _load_entries()
    if not entries:
        logger.warning("Knowledge base vazia, retrieval desabilitado")
        return ""

    scored = [(entry, _score(entry, query_tokens)) for entry in entries]
    top = sorted(scored, key=lambda x: x[1], reverse=True)[:top_n]
    top = [(e, s) for e, s in top if s >= _MIN_SCORE]

    if not top:
        logger.debug("Nenhum comando relevante para query: %s", query[:50])
        return ""

    lines = ["Comandos relevantes da base de conhecimento:"]
    for entry, score in top:
        lines.append(
            f"  • `{entry['cmd']}` — {entry['desc']}  [score={score}, cat={entry['category']}]"
        )

    logger.debug("Retrieved %d comandos para query: %s", len(top), query[:50])
    return "\n".join(lines)


def reload_cache() -> None:
    """Força recarregamento da knowledge base (útil em desenvolvimento)."""
    _load_entries.cache_clear()
    logger.info("Cache da knowledge base limpo")


def test(query: str = "como ver portas abertas?") -> None:
    """Testa o retriever com uma query de exemplo."""
    print(f"\n🔍 Query: {query}")
    print("-" * 60)
    result = retrieve(query)
    if result:
        print(result)
    else:
        print("(nenhum comando relevante encontrado)")
    print()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    # Testes de exemplo
    test_queries = [
        "como ver portas abertas no sistema?",
        "como listar arquivos por tamanho?",
        "como matar um processo pelo nome?",
        "como verificar uso de disco?",
        "container saindo com exit code 137",
        "serviço systemd não está iniciando",
        "como limpar imagens docker não utilizadas?",
    ]

    for q in test_queries:
        test(q)
