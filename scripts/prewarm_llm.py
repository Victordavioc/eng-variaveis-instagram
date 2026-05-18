"""Pre-aquece o cache do Gemini executando todos os prompts do notebook
fora do contexto do Jupyter, com rate limiting respeitoso.

Isso isola o gargalo: o notebook depois só lê do cache (rápido).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.gemini_client import GeminiClient
from src.data_loader import load_all

# 1. limpa entradas None do cache (falhas anteriores)
cache_path = ROOT / "data" / "processed" / "llm_cache.json"
if cache_path.exists():
    with open(cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)
    before = len(cache)
    cache = {k: v for k, v in cache.items() if v is not None}
    after = len(cache)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"Cache limpo: {before} -> {after} entradas válidas")

# 2. carrega data, aplica os mesmos filtros do notebook (Seção 2) para gerar
#    EXATAMENTE os mesmos prompts (mesma hash)
import pandas as pd
profiles_df, posts_df, comments_df = load_all()
profiles_df = profiles_df[
    (profiles_df["follower_count"] >= 1000) &
    (profiles_df["is_private"] == False) &
    (profiles_df["media_count"] >= 5)
].reset_index(drop=True)
valid_user_pks = set(profiles_df["pk"].astype(str))
posts_df = posts_df[posts_df["user_pk"].isin(valid_user_pks)].reset_index(drop=True)
valid_media_pks = set(posts_df["media_pk"].astype(str))
comments_df = comments_df[comments_df["media_pk"].isin(valid_media_pks)].reset_index(drop=True)
posts_df = posts_df.dropna(subset=["taken_at", "like_count", "media_pk"]).reset_index(drop=True)
posts_df["caption_text"] = posts_df["caption_text"].fillna("")
posts_df = posts_df.drop_duplicates(subset=["media_pk"]).reset_index(drop=True)
comments_df = comments_df.drop_duplicates(subset=["comment_pk"]).reset_index(drop=True)
posts_df = posts_df[(posts_df["like_count"] >= 0) & (posts_df["comment_count"].fillna(0) >= 0)].reset_index(drop=True)

print(f"posts a processar: {len(posts_df)}  comments: {len(comments_df)}")

llm = GeminiClient()
print(f"Modelo: {llm.model}")

THEMES = ["esporte", "lifestyle", "promocional", "humor", "noticias", "pessoal", "educacional", "outro"]
BATCH = 25
SLEEP_BETWEEN_CALLS = 4.5  # ~13 RPM, dentro do free tier do gemini-3-flash-preview


def build_theme_prompt(captions: list[str]) -> str:
    items = "\n".join(f"{i}. {c[:280].replace(chr(10),' ')}" for i, c in enumerate(captions))
    return (
        "Você classifica captions de Instagram em categorias temáticas.\n"
        f"Categorias possíveis: {', '.join(THEMES)}.\n"
        "Para cada caption abaixo, retorne JSON com a chave 'results', "
        "um array de objetos {\"index\": int, \"theme\": string}. "
        "Se a caption estiver vazia ou for ambígua, use 'outro'.\n\n"
        f"Captions:\n{items}"
    )


def build_entities_prompt(captions: list[str]) -> str:
    items = "\n".join(f"{i}. {c[:280].replace(chr(10),' ')}" for i, c in enumerate(captions))
    return (
        "Para cada caption de Instagram abaixo, extraia até 5 entidades nomeadas "
        "(marcas, produtos, pessoas, locais, eventos). Use o nome original quando possível.\n"
        "Retorne JSON {\"results\": [{\"index\": int, \"entities\": [string,...]}, ...]}. "
        "Se não houver entidades, retorne array vazio.\n\n"
        f"Captions:\n{items}"
    )


def build_sentiment_prompt(texts: list[str]) -> str:
    items = "\n".join(f"{i}. {t[:200].replace(chr(10),' ')}" for i, t in enumerate(texts))
    return (
        "Para cada comentário de Instagram abaixo, classifique o sentimento como "
        "'positivo', 'neutro' ou 'negativo'. Considere ironia, emojis e gírias.\n"
        "Retorne JSON {\"results\": [{\"index\": int, \"sentiment\": string}, ...]}.\n\n"
        f"Comentários:\n{items}"
    )


def warm_batches(items: list[str], prompt_builder, label: str, skip_empty=False):
    """Itera batches; chama LLM se não estiver em cache."""
    total = (len(items) + BATCH - 1) // BATCH
    misses = 0
    for i in range(0, len(items), BATCH):
        batch = items[i:i+BATCH]
        if skip_empty:
            non_empty_idx = [j for j, c in enumerate(batch) if c.strip()]
            if not non_empty_idx:
                continue
            sub = [batch[j] for j in non_empty_idx]
        else:
            sub = [t if t.strip() else "vazio" for t in batch]
        prompt = prompt_builder(sub)
        # checa cache sem disparar request
        key = llm._hash_key(llm.model, prompt)
        if key in llm._cache and llm._cache[key] is not None:
            continue
        misses += 1
        t0 = time.time()
        out = llm.generate_json(prompt)
        dt = time.time() - t0
        status = "ok" if isinstance(out, dict) else "FAIL"
        print(f"  [{label}] batch {i//BATCH+1}/{total} ({dt:.1f}s) -> {status}")
        time.sleep(SLEEP_BETWEEN_CALLS)
    print(f"  [{label}] {misses} chamadas novas, cache final: {len(llm._cache)}")


captions = posts_df["caption_text"].fillna("").tolist()
cmt_texts = comments_df["text"].fillna("").tolist()

print("\n=== themes ===")
warm_batches(captions, build_theme_prompt, "theme", skip_empty=True)
print("\n=== entities ===")
warm_batches(captions, build_entities_prompt, "entities", skip_empty=True)
print("\n=== sentiment ===")
warm_batches(cmt_texts, build_sentiment_prompt, "sentiment", skip_empty=False)

print("\n=== final ===")
with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)
none_count = sum(1 for v in cache.values() if v is None)
print(f"Cache total: {len(cache)}  válidas: {len(cache)-none_count}  None: {none_count}")
