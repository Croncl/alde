"""
Retrieval de comandos Linux relevantes a partir da knowledge_base.json.

Dado o texto de uma mensagem, extrai os N comandos mais relevantes por
sobreposição de keywords entre a query e os campos cmd/desc de cada entrada.
Usado para injetar contexto cirúrgico no prompt antes de chamar o modelo.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_KB_PATH = Path(__file__).parent / "knowledge_base.json"
_TOP_N = 6
_MIN_SCORE = 1


@lru_cache(maxsize=1)
def _load_entries() -> list[dict]:
    """Carrega e flatten o JSON em lista de entradas. Cached na startup."""
    with _KB_PATH.open(encoding="utf-8") as f:
        kb = json.load(f)

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
    return entries


def _tokenize(text: str) -> set[str]:
    """Extrai tokens alfanuméricos com 3+ caracteres, lowercase."""
    return {t for t in re.split(r"[^a-zA-ZÀ-ÿ0-9]+", text.lower()) if len(t) >= 3}


def _score(entry: dict, query_tokens: set[str]) -> int:
    """Conta sobreposição de tokens entre query e cmd+desc da entrada."""
    entry_tokens = _tokenize(entry["cmd"] + " " + entry["desc"])
    return len(query_tokens & entry_tokens)


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
    scored = [(entry, _score(entry, query_tokens)) for entry in entries]
    top = sorted(scored, key=lambda x: x[1], reverse=True)[:top_n]
    top = [(e, s) for e, s in top if s >= _MIN_SCORE]

    if not top:
        return ""

    lines = ["Comandos relevantes da base de conhecimento:"]
    for entry, _ in top:
        lines.append(f"  • `{entry['cmd']}` — {entry['desc']}")

    return "\n".join(lines)
