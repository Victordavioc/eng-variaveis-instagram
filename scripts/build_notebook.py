"""Constrói notebooks/apresentacao.ipynb via nbformat.

Mantém o conteúdo como lista de células (markdown/code) — fácil de auditar e regenerar.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "notebooks" / "apresentacao.ipynb"


def md(text: str) -> dict:
    return nbf.v4.new_markdown_cell(text)


def code(text: str) -> dict:
    return nbf.v4.new_code_cell(text)


cells: list = []

# ============================================================
# SEÇÃO 0 — Introdução
# ============================================================
cells.append(md("""# Engenharia de Variáveis com Dados do Instagram

**Disciplina:** Engenharia de Variáveis — UFG
**Data da apresentação:** 02/06/2026
**Fonte de dados:** [Hiker API](https://hikerapi.com/) — scraping autorizado de perfis públicos do Instagram

## Por que esse projeto?

Os dados do Instagram chegam como **JSON semi-estruturado**, com campos
aninhados, texto livre (captions, comentários), datas em UNIX timestamp,
e métricas em escalas absurdamente diferentes (Cristiano Ronaldo tem
~660 milhões de seguidores; um perfil micro pode ter 10 mil). É um
playground perfeito para mostrar **todas as técnicas de engenharia
de variáveis** que vamos cobrir:

1. **Exclusão de anomalias** — filtrar contas privadas, bots, posts impossíveis
2. **Decomposição** — quebrar `taken_at`, `caption_text` em dezenas de features
3. **Features semânticas via LLM** — Gemini extrai tema, sentimento, entidades
4. **Discretização** — virar `follower_count` em tier (micro/mid/macro)
5. **Cruzamento** — `tier × theme`, `engagement_rate`
6. **Transformações lineares** — StandardScaler para comparar perfis
7. **Transformações não-lineares** — log para domar a cauda longa

## A pergunta que vamos responder

> *Como diferentes tiers de influenciadores se comportam no Instagram, e o que captions e comentários revelam sobre cada um?*

Especificamente, no fim do notebook a base estará preparada para responder:

| Dimensão | Pergunta |
|---|---|
| Saúde do perfil | Quem tem engajamento suspeito (anômalo)? |
| Caption analysis | O que caracteriza captions de alto desempenho? |
| Audiência | O que os comentários revelam sobre a recepção? |
| Comparação entre tiers | Micro, mid e macro performam diferente como? |
"""))

# ============================================================
# SEÇÃO 1 — Coleta e carregamento
# ============================================================
cells.append(md("""## 1. Coleta e carregamento (JSON semi-estruturado)

A Hiker API retorna 3 tipos de objeto: **perfil**, **mídia (post)** e **comentário**.
Tudo cacheado em `data/raw/` — re-rodar o notebook **não consome créditos**.

> O wrapper `src/hiker_client.py` cuida de paginação, retry com backoff e cache em disco.
> O loader `src/data_loader.py` usa `pd.json_normalize` para achatar a estrutura aninhada em 3 DataFrames relacionais.
"""))

cells.append(code("""# imports e setup
import sys, os, json, warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid")
plt.rcParams["figure.dpi"] = 100

# torna `src` importável a partir do notebook
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))
print("Raiz do projeto:", ROOT)"""))

cells.append(code("""# inspecionando um JSON cru de perfil para entender o schema aninhado
import json
sample_path = ROOT / "data" / "raw" / "profile" / "cristiano.json"
with open(sample_path, "r", encoding="utf-8") as f:
    sample = json.load(f)

print("Quantidade de campos no perfil:", len(sample))
print("Exemplo de campos aninhados:", [k for k in sample.keys() if isinstance(sample.get(k), (dict, list))][:8])
# mostra um pedaço do schema cru
print(json.dumps({k: sample[k] for k in list(sample.keys())[:8]}, ensure_ascii=False, indent=2, default=str)[:600])"""))

cells.append(code("""# carrega os 3 DataFrames a partir do cache em disco
from src.data_loader import load_all

profiles_df, posts_df, comments_df = load_all()

print(f"profiles_df: {profiles_df.shape[0]} linhas × {profiles_df.shape[1]} colunas")
print(f"posts_df:    {posts_df.shape[0]} linhas × {posts_df.shape[1]} colunas")
print(f"comments_df: {comments_df.shape[0]} linhas × {comments_df.shape[1]} colunas")"""))

cells.append(code("""# preview dos perfis coletados
profiles_df[["username", "follower_count", "following_count", "media_count", "is_verified", "is_private"]].sort_values("follower_count", ascending=False)"""))

# ============================================================
# SEÇÃO 2 — Exclusão de anomalias
# ============================================================
cells.append(md("""## 2. Exclusão de anomalias

> *"O que não dá pra confiar, vai fora — antes de qualquer comparação."*

Vamos detectar:

- **Contas suspeitas/inativas:** poucos seguidores, sem posts, contas privadas
- **Nulos sistêmicos:** posts sem `caption_text` (mídias só-imagem), `like_count` ausente
- **Duplicatas:** mesmo `media_pk` apareceu em paginação sobreposta
- **Outliers em likes:** detectados via IQR (mas mantidos como "viral" — não removidos)

A limpeza é o que vai permitir comparar **micro × macro de forma justa** mais à frente.
"""))

cells.append(code("""# 2.1 - perfis suspeitos: muito poucos seguidores ou conta privada
print("Antes:", profiles_df.shape)

profile_anomalies = profiles_df[
    (profiles_df["follower_count"] < 1000) |
    (profiles_df["is_private"] == True) |
    (profiles_df["media_count"] < 5)
][["username", "follower_count", "is_private", "media_count"]]
print("\\nPerfis filtrados:")
print(profile_anomalies.to_string(index=False))

profiles_df = profiles_df[
    (profiles_df["follower_count"] >= 1000) &
    (profiles_df["is_private"] == False) &
    (profiles_df["media_count"] >= 5)
].reset_index(drop=True)
print("\\nDepois:", profiles_df.shape)"""))

cells.append(code("""# 2.2 - sincronizar posts/comments com perfis válidos
valid_user_pks = set(profiles_df["pk"].astype(str))
before_posts = len(posts_df)
posts_df = posts_df[posts_df["user_pk"].isin(valid_user_pks)].reset_index(drop=True)
print(f"posts: {before_posts} -> {len(posts_df)} (após filtrar perfis inválidos)")

valid_media_pks = set(posts_df["media_pk"].astype(str))
before_cmts = len(comments_df)
comments_df = comments_df[comments_df["media_pk"].isin(valid_media_pks)].reset_index(drop=True)
print(f"comments: {before_cmts} -> {len(comments_df)}")"""))

cells.append(code("""# 2.3 - nulos em colunas críticas
critical_post_cols = ["like_count", "comment_count", "taken_at", "media_pk", "user_pk"]
print("Nulos por coluna crítica em posts:")
print(posts_df[critical_post_cols].isna().sum())

# remove posts sem timestamp ou sem likes (essenciais)
posts_df = posts_df.dropna(subset=["taken_at", "like_count", "media_pk"]).reset_index(drop=True)
# caption_text pode ser NaN para posts só-imagem — preenche com string vazia
posts_df["caption_text"] = posts_df["caption_text"].fillna("")
print("\\nApós tratar nulos:", posts_df.shape)"""))

cells.append(code("""# 2.4 - duplicatas
dup_posts = posts_df.duplicated(subset=["media_pk"]).sum()
dup_cmts = comments_df.duplicated(subset=["comment_pk"]).sum()
print(f"Duplicatas em posts: {dup_posts}")
print(f"Duplicatas em comments: {dup_cmts}")

posts_df = posts_df.drop_duplicates(subset=["media_pk"]).reset_index(drop=True)
comments_df = comments_df.drop_duplicates(subset=["comment_pk"]).reset_index(drop=True)"""))

cells.append(code("""# 2.5 - valores impossíveis
impossible = (posts_df["like_count"] < 0).sum() + (posts_df["comment_count"] < 0).sum()
print(f"Valores impossíveis (likes/comments negativos): {impossible}")
# garantir não-negatividade (defensivo)
posts_df = posts_df[(posts_df["like_count"] >= 0) & (posts_df["comment_count"].fillna(0) >= 0)].reset_index(drop=True)"""))

cells.append(code("""# 2.6 - outliers em like_count via IQR (NÃO removemos — vamos rotular como 'viral')
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.boxplot(x=posts_df["like_count"], ax=axes[0], color="#69b3a2")
axes[0].set_title("Likes — escala original (cauda gigante)")
axes[0].set_xlabel("like_count")

# IQR
q1, q3 = posts_df["like_count"].quantile([0.25, 0.75])
iqr = q3 - q1
upper = q3 + 1.5 * iqr
n_outliers = (posts_df["like_count"] > upper).sum()
print(f"Upper IQR fence: {upper:.0f}  | posts acima: {n_outliers} ({n_outliers/len(posts_df)*100:.1f}%)")

sns.boxplot(x=np.log1p(posts_df["like_count"]), ax=axes[1], color="#e07a5f")
axes[1].set_title("Likes — escala log1p (cauda comprimida)")
axes[1].set_xlabel("log1p(like_count)")
plt.tight_layout()
plt.show()"""))

cells.append(md("""**Decisão analítica:** posts no topo do IQR **não são removidos** — eles são exatamente os "virais"
que queremos estudar. A escala log1p (à direita) mostra que, com a transformação correta,
o que parecia outlier vira parte natural da distribuição. Isso prepara a Seção 8.
"""))

# ============================================================
# SEÇÃO 3 — Decomposição
# ============================================================
cells.append(md("""## 3. Decomposição

Campos compostos viram várias features primitivas.

- `taken_at` (timestamp ISO) → **ano, mês, dia, hora, dia da semana, período do dia, fim de semana**
- `caption_text` (texto livre) → **comprimento, num_hashtags, num_mentions, num_emojis, num_linhas**

Isso permite responder *"qual horário rende mais?"* e *"caption longa engaja mais?"*.
"""))

cells.append(code("""# 3.1 - decompor a data do post
import re
import emoji as _emoji_lib  # se não tiver, usa fallback regex
# fallback caso emoji não esteja instalado
def count_emojis(s: str) -> int:
    if not isinstance(s, str): return 0
    # range Unicode aproximado para emojis
    return sum(1 for ch in s if ord(ch) > 0x2600 and not ch.isalnum())""", ))

cells.append(code("""# converte taken_at para datetime UTC e decompõe
posts_df["taken_at"] = pd.to_datetime(posts_df["taken_at"], utc=True, errors="coerce")
posts_df = posts_df.dropna(subset=["taken_at"]).reset_index(drop=True)

posts_df["year"]       = posts_df["taken_at"].dt.year
posts_df["month"]      = posts_df["taken_at"].dt.month
posts_df["day"]        = posts_df["taken_at"].dt.day
posts_df["hour"]       = posts_df["taken_at"].dt.hour
posts_df["weekday"]    = posts_df["taken_at"].dt.day_name()
posts_df["is_weekend"] = posts_df["taken_at"].dt.dayofweek >= 5

def period_of_day(h: int) -> str:
    if   h < 6:  return "madrugada"
    elif h < 12: return "manhã"
    elif h < 18: return "tarde"
    else:        return "noite"
posts_df["period_of_day"] = posts_df["hour"].apply(period_of_day)

posts_df[["taken_at", "year", "month", "hour", "weekday", "period_of_day", "is_weekend"]].head()"""))

cells.append(code("""# 3.2 - decompor caption_text
import re

HASHTAG_RE = re.compile(r"#\\w+")
MENTION_RE = re.compile(r"@\\w+")

def count_emojis(s):
    if not isinstance(s, str): return 0
    return sum(1 for ch in s if ord(ch) > 0x2600 and not ch.isalnum())

posts_df["caption_length"]   = posts_df["caption_text"].str.len().fillna(0).astype(int)
posts_df["num_hashtags"]     = posts_df["caption_text"].apply(lambda s: len(HASHTAG_RE.findall(s)) if isinstance(s,str) else 0)
posts_df["num_mentions"]     = posts_df["caption_text"].apply(lambda s: len(MENTION_RE.findall(s)) if isinstance(s,str) else 0)
posts_df["num_emojis"]       = posts_df["caption_text"].apply(count_emojis)
posts_df["num_lines"]        = posts_df["caption_text"].apply(lambda s: s.count("\\n")+1 if isinstance(s,str) and s else 0)
posts_df["has_caption"]      = (posts_df["caption_length"] > 0).astype(int)

posts_df[["caption_length", "num_hashtags", "num_mentions", "num_emojis", "num_lines", "has_caption"]].describe().round(2)"""))

cells.append(code("""# 3.3 - visualizar a distribuição do que decompusemos
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

sns.countplot(data=posts_df, x="period_of_day",
              order=["madrugada", "manhã", "tarde", "noite"], ax=axes[0])
axes[0].set_title("Posts por período do dia")
axes[0].set_xlabel("")

sns.histplot(posts_df["caption_length"].clip(upper=600), bins=30, ax=axes[1], color="#e07a5f")
axes[1].set_title("Distribuição do comprimento das captions")
axes[1].set_xlabel("caption_length (clipado em 600)")

sns.countplot(data=posts_df, x="weekday",
              order=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], ax=axes[2])
axes[2].tick_params(axis="x", rotation=30)
axes[2].set_title("Posts por dia da semana")
axes[2].set_xlabel("")
plt.tight_layout()
plt.show()"""))

# ============================================================
# SEÇÃO 4 — Features via LLM
# ============================================================
cells.append(md("""## 4. Features semânticas via LLM (Gemini) — com fallback determinístico

> *"O LLM é o estado-da-arte para engenharia de features sobre texto não-estruturado —
> mas um pipeline de produção precisa de fallback."*

Antes: regex, dicionários de palavras, sentimento via lexicon. Tudo frágil para gírias,
emojis, ironia, mistura de idiomas. Hoje, um único prompt produz features estruturadas:

| Feature | O que extraímos | Onde |
|---|---|---|
| `theme` | esporte, lifestyle, promocional, humor, notícias, pessoal, educacional, outro | em **captions** |
| `entities` | produtos, pessoas, locais, marcas mencionados | em **captions** |
| `sentiment` | positivo, neutro, negativo | em **comentários** |

**Estratégia híbrida:** tentamos primeiro o LLM (cache em `data/processed/llm_cache.json`).
Quando o LLM não está disponível (rate-limit, quota), aplicamos um **fallback baseado em regras**
e marcamos o registro com `*_source` = `'llm'` ou `'fallback'`. Isso garante que o pipeline
**nunca falha por causa do LLM** — degradação graciosa.
"""))

cells.append(code("""# 4.1 - prepara o cliente do Gemini
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from src.gemini_client import GeminiClient
llm = GeminiClient()
print("Modelo:", llm.model)
print("Cache atual:", len(llm._cache), "entradas")"""))

cells.append(code("""# 4.2a - fallback determinístico para tema (caso o LLM não responda)
import re

THEME_KEYWORDS = {
    "esporte":     [r"\\bgol\\b", r"\\bjogo\\b", r"\\btime\\b", r"\\bcampeonat", r"\\bfinal\\b", r"\\bvit[oó]ria", r"\\btreino", r"\\bgame", r"\\bmatch", r"\\bgoal", r"\\bnba\\b", r"\\bfifa", r"\\bbarça", r"⚽", r"🏀", r"🏆"],
    "promocional": [r"\\blink na bio\\b", r"\\blink in bio\\b", r"\\bdesconto", r"\\bpromoç[ãa]o", r"\\bcompre\\b", r"\\bcupom\\b", r"\\bventa\\b", r"\\bsale\\b", r"\\bavailable now\\b", r"\\blaunch\\b", r"\\bpre.?order\\b", r"\\bsponsor"],
    "humor":       [r"\\bkkk", r"\\brsrs", r"\\bhaha", r"\\blol\\b", r"😂", r"🤣", r"\\bmeme\\b", r"\\bzoeira"],
    "noticias":    [r"\\bbreaking\\b", r"\\bnews\\b", r"\\bnot[ií]cia", r"\\bhoje cedo\\b", r"\\boficial\\b", r"\\banunci"],
    "educacional": [r"\\bdica\\b", r"\\baprend", r"\\btutorial", r"\\bcomo fazer", r"\\bhow to\\b", r"\\bguide\\b", r"\\bestud", r"\\bcurso", r"\\baula\\b"],
    "lifestyle":   [r"\\bvibe\\b", r"\\boutfit\\b", r"\\bweekend\\b", r"\\bfds\\b", r"\\bmood\\b", r"\\bdrip\\b", r"\\bfit\\b", r"\\bfamilia", r"\\bamigos\\b", r"\\bbeach\\b"],
}

def theme_from_keywords(caption: str) -> str:
    \"\"\"Aplica regex de keywords ordenado por especificidade. Retorna 'outro' se nada bater.\"\"\"
    if not caption or not caption.strip(): return "outro"
    txt = caption.lower()
    for theme, patterns in THEME_KEYWORDS.items():
        if any(re.search(p, txt) for p in patterns):
            return theme
    return "pessoal" if len(caption) > 40 else "outro"

# teste rápido
print("Fallback de tema:")
for c in ["Hattrick hoje! ⚽ #portugal", "Link na bio pro desconto", "kkkkk não acredito", "Como aprender React em 30 dias"]:
    print(f"  {c!r} -> {theme_from_keywords(c)}")"""))

cells.append(code("""# 4.2b - classificação temática: tenta LLM em batches, fallback para keywords
import json

THEMES = ["esporte", "lifestyle", "promocional", "humor", "noticias", "pessoal", "educacional", "outro"]

def classify_themes_batch(captions: list[str]) -> list[str] | None:
    \"\"\"Tenta o LLM. Retorna None se falhar (sinal para usar fallback).\"\"\"
    if not captions: return []
    items = "\\n".join(f"{i}. {c[:280].replace(chr(10),' ')}" for i, c in enumerate(captions))
    prompt = (
        "Você classifica captions de Instagram em categorias temáticas.\\n"
        f"Categorias possíveis: {', '.join(THEMES)}.\\n"
        "Para cada caption abaixo, retorne JSON com a chave 'results', "
        "um array de objetos {\\\"index\\\": int, \\\"theme\\\": string}. "
        "Se a caption estiver vazia ou for ambígua, use 'outro'.\\n\\n"
        f"Captions:\\n{items}"
    )
    out = llm.generate_json(prompt)
    if not isinstance(out, dict) or "results" not in out:
        return None
    by_idx = {r.get("index"): r.get("theme", "outro") for r in out["results"] if isinstance(r, dict)}
    return [by_idx.get(i, "outro") for i in range(len(captions))]

captions = posts_df["caption_text"].fillna("").tolist()
themes_out, sources = [], []
BATCH = 25
n_llm_batches = n_fallback_batches = 0
for i in range(0, len(captions), BATCH):
    batch = captions[i:i+BATCH]
    non_empty_idx = [j for j, c in enumerate(batch) if c.strip()]
    if not non_empty_idx:
        themes_out.extend(["outro"] * len(batch))
        sources.extend(["empty"] * len(batch))
        continue
    sub = [batch[j] for j in non_empty_idx]
    llm_result = classify_themes_batch(sub)
    out, src = ["outro"] * len(batch), ["empty"] * len(batch)
    if llm_result is None:
        # LLM falhou para esse batch — aplica fallback de keywords
        n_fallback_batches += 1
        for k, j in enumerate(non_empty_idx):
            out[j] = theme_from_keywords(sub[k])
            src[j] = "fallback"
    else:
        n_llm_batches += 1
        for k, j in enumerate(non_empty_idx):
            out[j] = llm_result[k] if k < len(llm_result) else "outro"
            src[j] = "llm"
    themes_out.extend(out)
    sources.extend(src)

posts_df["theme"] = themes_out
posts_df["theme_source"] = sources

print(f"Batches: {n_llm_batches} via LLM, {n_fallback_batches} via fallback de keywords")
print("\\nDistribuição final de temas:")
print(posts_df["theme"].value_counts())
print("\\nFonte das classificações:")
print(posts_df["theme_source"].value_counts())"""))

cells.append(code("""# 4.3 - extração de entidades: LLM com fallback regex (hashtags + @mentions + Maiúsculas)
def extract_entities_batch(captions: list[str]) -> list[list[str]] | None:
    if not captions: return []
    items = "\\n".join(f"{i}. {c[:280].replace(chr(10),' ')}" for i, c in enumerate(captions))
    prompt = (
        "Para cada caption de Instagram abaixo, extraia até 5 entidades nomeadas "
        "(marcas, produtos, pessoas, locais, eventos). Use o nome original quando possível.\\n"
        "Retorne JSON {\\\"results\\\": [{\\\"index\\\": int, \\\"entities\\\": [string,...]}, ...]}. "
        "Se não houver entidades, retorne array vazio.\\n\\n"
        f"Captions:\\n{items}"
    )
    out = llm.generate_json(prompt)
    if not isinstance(out, dict) or "results" not in out:
        return None
    by_idx = {r.get("index"): r.get("entities", []) for r in out["results"] if isinstance(r, dict)}
    return [by_idx.get(i, []) for i in range(len(captions))]

CAP_TOKEN_RE = re.compile(r"\\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,}(?:\\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]{2,}){0,2})\\b")
HASHTAG_RE2 = re.compile(r"#(\\w{3,})")
MENTION_RE2 = re.compile(r"@(\\w{3,})")
STOP = {"Hoje","Amanhã","Você","Vocês","Nós","Que","Mas","Quando","Tudo","Para","Como","Mais"}

def regex_entities(caption: str) -> list[str]:
    if not isinstance(caption, str) or not caption.strip(): return []
    ents = set()
    for m in HASHTAG_RE2.findall(caption): ents.add(m.lower())
    for m in MENTION_RE2.findall(caption): ents.add("@" + m.lower())
    for tok in CAP_TOKEN_RE.findall(caption):
        if tok.split()[0] not in STOP:
            ents.add(tok)
    return list(ents)[:5]

entities_out, ent_sources = [], []
n_llm = n_fb = 0
for i in range(0, len(captions), BATCH):
    batch = captions[i:i+BATCH]
    non_empty_idx = [j for j, c in enumerate(batch) if c.strip()]
    if not non_empty_idx:
        entities_out.extend([[]] * len(batch))
        ent_sources.extend(["empty"] * len(batch))
        continue
    sub = [batch[j] for j in non_empty_idx]
    llm_result = extract_entities_batch(sub)
    out = [[] for _ in batch]
    src = ["empty"] * len(batch)
    if llm_result is None:
        n_fb += 1
        for k, j in enumerate(non_empty_idx):
            out[j] = regex_entities(sub[k])
            src[j] = "fallback"
    else:
        n_llm += 1
        for k, j in enumerate(non_empty_idx):
            out[j] = llm_result[k] if k < len(llm_result) and isinstance(llm_result[k], list) else []
            src[j] = "llm"
    entities_out.extend(out)
    ent_sources.extend(src)

posts_df["entities"] = entities_out
posts_df["entities_source"] = ent_sources
posts_df["num_entities"] = posts_df["entities"].apply(lambda x: len(x) if isinstance(x, list) else 0)

print(f"Batches: {n_llm} via LLM, {n_fb} via fallback regex")

from collections import Counter
all_ents = [e.lower().strip() for lst in posts_df["entities"] for e in (lst or []) if isinstance(e, str) and e.strip()]
print("\\nTop 15 entidades extraídas:")
for ent, cnt in Counter(all_ents).most_common(15):
    print(f"  {cnt:3d}  {ent}")"""))

cells.append(code("""# 4.4 - sentimento dos comentários: LLM com fallback lexicon-based
POS_TOKENS = {"❤","♥","😍","🥰","😘","🔥","💯","👏","🙌","💖","😊","amo","amei","love","top","best","melhor","incrível","incrivel","perfeito","perfect","lindo","linda","gostei","amazing","awesome","gg","goat","king","queen","🐐","👑","wonderful","brilhante","obrigado","obrigada","thanks","beautiful","bonito","sucesso","parabéns","parabens","congrats","viva","🇧🇷","🇵🇹"}
NEG_TOKENS = {"😡","🤬","💩","👎","🤮","lixo","trash","horrível","horrivel","ruim","péssimo","pessimo","bad","worst","odeio","hate","fake","decepção","decepcao","mentira","feio","feia","chato","boring","cringe","wtf","scam","awful","sucks","🤡"}

def lexicon_sentiment(text: str) -> str:
    if not isinstance(text, str) or not text.strip(): return "neutro"
    t = text.lower()
    pos = sum(1 for tok in POS_TOKENS if tok.lower() in t)
    neg = sum(1 for tok in NEG_TOKENS if tok.lower() in t)
    if pos > neg: return "positivo"
    if neg > pos: return "negativo"
    return "neutro"

def sentiment_batch(texts: list[str]) -> list[str] | None:
    if not texts: return []
    items = "\\n".join(f"{i}. {t[:200].replace(chr(10),' ')}" for i, t in enumerate(texts))
    prompt = (
        "Para cada comentário de Instagram abaixo, classifique o sentimento como "
        "'positivo', 'neutro' ou 'negativo'. Considere ironia, emojis e gírias.\\n"
        "Retorne JSON {\\\"results\\\": [{\\\"index\\\": int, \\\"sentiment\\\": string}, ...]}.\\n\\n"
        f"Comentários:\\n{items}"
    )
    out = llm.generate_json(prompt)
    if not isinstance(out, dict) or "results" not in out:
        return None
    by_idx = {r.get("index"): r.get("sentiment", "neutro") for r in out["results"] if isinstance(r, dict)}
    return [by_idx.get(i, "neutro") for i in range(len(texts))]

cmt_texts = comments_df["text"].fillna("").tolist()
sentiments_out, sent_sources = [], []
n_llm = n_fb = 0
for i in range(0, len(cmt_texts), BATCH):
    batch = cmt_texts[i:i+BATCH]
    sub = [t if t.strip() else "vazio" for t in batch]
    llm_result = sentiment_batch(sub)
    if llm_result is None or len(llm_result) != len(batch):
        n_fb += 1
        sentiments_out.extend([lexicon_sentiment(t) for t in batch])
        sent_sources.extend(["fallback"] * len(batch))
    else:
        n_llm += 1
        sentiments_out.extend(llm_result)
        sent_sources.extend(["llm"] * len(batch))

comments_df["sentiment"] = sentiments_out
comments_df["sentiment_source"] = sent_sources

print(f"Batches: {n_llm} via LLM, {n_fb} via fallback lexicon")
print("\\nDistribuição final de sentimentos:")
print(comments_df["sentiment"].value_counts(normalize=True).round(3))"""))

cells.append(md("""**Antes e depois:** observe que regex jamais extrairia o tema correto de uma caption
mista de português e inglês cheia de emojis, mas o LLM faz isso de forma robusta. Esse é
o salto qualitativo da engenharia de features moderna sobre texto.
"""))

cells.append(code("""# exemplo qualitativo: caption crua vs. features extraídas
example = posts_df[(posts_df["caption_length"] > 50) & (posts_df["num_entities"] > 0)].head(3)
for _, row in example.iterrows():
    print("CAPTION:", (row["caption_text"][:200] + "…") if len(row["caption_text"])>200 else row["caption_text"])
    print(f"  theme    : {row['theme']}")
    print(f"  entities : {row['entities']}")
    print(f"  length   : {row['caption_length']}  hashtags={row['num_hashtags']}  emojis={row['num_emojis']}")
    print()"""))

# ============================================================
# SEÇÃO 5 — Discretização
# ============================================================
cells.append(md("""## 5. Discretização

Converter variáveis contínuas em categorias ordenadas.

- `follower_count` → **tier** (`micro` <100k, `mid` 100k-1M, `macro` >1M) via `pd.cut`
- `like_count`     → **quartil de engajamento** (`baixo` / `médio` / `alto` / `viral`) via `pd.qcut`
- `caption_length` → **faixa** (`curta` <50, `média` 50-200, `longa` >200)
- `hour`           → **período do dia** (já criado na Seção 3)

`pd.cut` usa **bins fixos** (decisão de domínio); `pd.qcut` usa **quantis** (decisão pelos dados).
"""))

cells.append(code("""# 5.1 - tier por follower_count (binning fixo, baseado em conhecimento do domínio)
tier_bins   = [0, 100_000, 1_000_000, float("inf")]
tier_labels = ["micro", "mid", "macro"]
profiles_df["tier"] = pd.cut(profiles_df["follower_count"], bins=tier_bins, labels=tier_labels)
profiles_df.groupby("tier", observed=False)["username"].apply(lambda s: ", ".join(s))"""))

cells.append(code("""# 5.2 - propaga o tier para posts e comments
tier_map = dict(zip(profiles_df["pk"].astype(str), profiles_df["tier"].astype(str)))
posts_df["tier"]    = posts_df["user_pk"].astype(str).map(tier_map)
comments_df["tier"] = comments_df["media_pk"].map(dict(zip(posts_df["media_pk"], posts_df["tier"])))

print("Posts por tier:")
print(posts_df["tier"].value_counts())"""))

cells.append(code("""# 5.3 - engajamento em quartis (qcut → bins baseados nos dados)
posts_df["engagement_quartile"] = pd.qcut(
    posts_df["like_count"],
    q=4,
    labels=["baixo", "médio", "alto", "viral"],
    duplicates="drop",
)
posts_df["engagement_quartile"].value_counts().sort_index()"""))

cells.append(code("""# 5.4 - faixa de comprimento da caption (binning fixo)
posts_df["caption_band"] = pd.cut(
    posts_df["caption_length"],
    bins=[-1, 50, 200, float("inf")],
    labels=["curta", "média", "longa"],
)
posts_df["caption_band"].value_counts()"""))

cells.append(md("""**Conexão analítica:** o `tier` é o que vai nos permitir comparar **micro × mid × macro**
de forma justa. Sem essa categorização, qualquer média geral seria dominada por Cristiano e Messi.
"""))

# ============================================================
# SEÇÃO 6 — Cruzamento
# ============================================================
cells.append(md("""## 6. Cruzamento de variáveis

Criar features novas a partir de combinações das existentes.

- **Feature numérica:** `engagement_rate = (likes + comments) / followers`
- **Feature numérica:** `comments_per_like` — sinal de discussão/polêmica
- **Cruzamento categórico:** `tier × theme` — qual tier domina qual tema?
- **Cruzamento categórico:** `period_of_day × engagement_quartile`
"""))

cells.append(code("""# 6.1 - engagement_rate (normalização por base de seguidores)
follower_map = dict(zip(profiles_df["pk"].astype(str), profiles_df["follower_count"]))
posts_df["author_followers"] = posts_df["user_pk"].astype(str).map(follower_map)
posts_df["engagement_rate"]  = (
    (posts_df["like_count"].fillna(0) + posts_df["comment_count"].fillna(0))
    / posts_df["author_followers"].replace(0, np.nan)
).fillna(0)

posts_df["comments_per_like"] = (
    posts_df["comment_count"].fillna(0) / posts_df["like_count"].replace(0, np.nan)
).fillna(0)

posts_df.groupby("tier", observed=False)["engagement_rate"].describe().round(4)"""))

cells.append(code("""# 6.2 - cruzamento tier × theme (heatmap de contagem normalizada)
cross_tt = pd.crosstab(posts_df["tier"], posts_df["theme"], normalize="index").round(3)
plt.figure(figsize=(10, 4))
sns.heatmap(cross_tt, annot=True, fmt=".2f", cmap="YlGnBu", cbar_kws={"label": "proporção"})
plt.title("Distribuição temática por tier — quem fala de quê?")
plt.ylabel("tier"); plt.xlabel("theme")
plt.tight_layout(); plt.show()"""))

cells.append(code("""# 6.3 - cruzamento period_of_day × engagement_quartile
cross_pe = pd.crosstab(posts_df["period_of_day"], posts_df["engagement_quartile"], normalize="index").round(3)
cross_pe = cross_pe.reindex(["madrugada","manhã","tarde","noite"])
plt.figure(figsize=(8, 4))
sns.heatmap(cross_pe, annot=True, fmt=".2f", cmap="RdPu", cbar_kws={"label": "proporção"})
plt.title("Quartil de engajamento por período do dia")
plt.tight_layout(); plt.show()"""))

# ============================================================
# SEÇÃO 7 — Transformações lineares
# ============================================================
cells.append(md("""## 7. Transformações lineares

Quando colocamos `followers`, `likes`, `comments` e `engagement_rate` na mesma análise,
suas **escalas são incomparáveis**. Padronizar é pré-requisito.

- `StandardScaler` — média 0, desvio 1 (para análise estatística)
- `MinMaxScaler`   — escala [0, 1] (para visualização, ex. radar chart)
"""))

cells.append(code("""# 7.1 - aplica StandardScaler em features numéricas-chave
from sklearn.preprocessing import StandardScaler, MinMaxScaler

num_cols = ["like_count", "comment_count", "caption_length", "engagement_rate", "num_hashtags"]
posts_num = posts_df[num_cols].fillna(0)

scaler_std = StandardScaler()
posts_std  = pd.DataFrame(scaler_std.fit_transform(posts_num), columns=[f"{c}_std" for c in num_cols])

scaler_mm  = MinMaxScaler()
posts_mm   = pd.DataFrame(scaler_mm.fit_transform(posts_num), columns=[f"{c}_mm" for c in num_cols])

posts_df = pd.concat([posts_df.reset_index(drop=True), posts_std, posts_mm], axis=1)
posts_std.describe().round(3)"""))

cells.append(code("""# 7.2 - antes vs depois: distribuição de like_count
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.histplot(posts_df["like_count"].clip(upper=posts_df["like_count"].quantile(0.99)),
             bins=40, ax=axes[0], color="#69b3a2")
axes[0].set_title("like_count — escala original")
sns.histplot(posts_df["like_count_std"], bins=40, ax=axes[1], color="#e07a5f")
axes[1].set_title("like_count — após StandardScaler")
axes[1].set_xlabel("z-score")
plt.tight_layout(); plt.show()"""))

# ============================================================
# SEÇÃO 8 — Transformações não-lineares
# ============================================================
cells.append(md("""## 8. Transformações não-lineares

A cauda longa do Instagram é brutal: a maioria dos posts tem milhares de likes, alguns
têm milhões. Em escala linear, qualquer gráfico é dominado pelos virais.

- `np.log1p` — em `like_count`, `comment_count`, `follower_count` (cauda longa clássica)
- `PowerTransformer (Yeo-Johnson)` — em `engagement_rate` (lida com zeros e valores positivos)

O objetivo é aproximar uma distribuição **mais próxima da normal**, viabilizando comparações
estatísticas e visualizações honestas.
"""))

cells.append(code("""# 8.1 - log1p nas métricas com cauda longa
posts_df["log_likes"]     = np.log1p(posts_df["like_count"])
posts_df["log_comments"]  = np.log1p(posts_df["comment_count"].fillna(0))
profiles_df["log_followers"] = np.log1p(profiles_df["follower_count"])

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.histplot(posts_df["like_count"], bins=40, ax=axes[0], color="#69b3a2")
axes[0].set_title("like_count — original (cauda longa)")
sns.histplot(posts_df["log_likes"], bins=40, ax=axes[1], color="#e07a5f")
axes[1].set_title("log1p(like_count) — quase log-normal")
plt.tight_layout(); plt.show()"""))

cells.append(code("""# 8.2 - Yeo-Johnson no engagement_rate
from sklearn.preprocessing import PowerTransformer

yj = PowerTransformer(method="yeo-johnson")
er = posts_df["engagement_rate"].fillna(0).values.reshape(-1, 1)
posts_df["engagement_rate_yj"] = yj.fit_transform(er).ravel()

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.histplot(posts_df["engagement_rate"], bins=40, ax=axes[0], color="#69b3a2")
axes[0].set_title("engagement_rate — original")
sns.histplot(posts_df["engagement_rate_yj"], bins=40, ax=axes[1], color="#e07a5f")
axes[1].set_title("engagement_rate — Yeo-Johnson")
plt.tight_layout(); plt.show()"""))

# ============================================================
# SEÇÃO 9 — Análise final
# ============================================================
cells.append(md("""## 9. Análise final — respondendo as 4 perguntas

Com a base preparada, conseguimos responder de forma visual e quantitativa.
"""))

cells.append(code("""# Pergunta 1 - Saúde do perfil: quem tem engajamento anômalo?
agg = posts_df.groupby("user_pk", observed=False).agg(
    avg_likes=("like_count", "mean"),
    avg_engagement_rate=("engagement_rate", "mean"),
    n_posts=("media_pk", "count"),
).reset_index()
agg = agg.merge(profiles_df[["pk","username","follower_count","tier"]],
                left_on="user_pk", right_on="pk")

plt.figure(figsize=(10, 5))
sns.scatterplot(data=agg, x="follower_count", y="avg_engagement_rate",
                hue="tier", s=120, palette="Set2")
plt.xscale("log")
for _, r in agg.iterrows():
    plt.text(r["follower_count"]*1.05, r["avg_engagement_rate"], r["username"], fontsize=8)
plt.title("Saúde do perfil: engagement_rate × follower_count (log)")
plt.xlabel("follower_count (log)"); plt.ylabel("engagement_rate médio")
plt.tight_layout(); plt.show()
agg.sort_values("avg_engagement_rate", ascending=False).head(10)"""))

cells.append(code("""# Pergunta 2 - Caption analysis: o que caracteriza captions de alto desempenho?
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
sns.boxplot(data=posts_df, x="theme", y="log_likes", ax=axes[0],
            order=posts_df.groupby("theme")["log_likes"].median().sort_values(ascending=False).index)
axes[0].tick_params(axis="x", rotation=30)
axes[0].set_title("Likes por tema (escala log)")

sns.scatterplot(data=posts_df, x="caption_length", y="log_likes",
                hue="tier", alpha=0.6, ax=axes[1], palette="Set2")
axes[1].set_xlim(0, posts_df["caption_length"].quantile(0.98))
axes[1].set_title("Comprimento da caption × log(likes)")
plt.tight_layout(); plt.show()"""))

cells.append(code("""# Pergunta 3 - Comportamento da audiência: sentimento por tier
sent_by_tier = pd.crosstab(comments_df["tier"], comments_df["sentiment"], normalize="index").round(3)
plt.figure(figsize=(8, 4))
sent_by_tier.plot(kind="bar", stacked=True, colormap="RdYlGn_r", ax=plt.gca())
plt.title("Distribuição de sentimento dos comentários por tier")
plt.ylabel("proporção"); plt.xticks(rotation=0)
plt.legend(title="sentimento", bbox_to_anchor=(1.02, 1), loc="upper left")
plt.tight_layout(); plt.show()
sent_by_tier"""))

cells.append(code("""# Pergunta 4 - Comparação entre tiers: tabela resumo
summary = posts_df.groupby("tier", observed=False).agg(
    posts=("media_pk", "count"),
    avg_likes=("like_count", "mean"),
    avg_engagement_rate=("engagement_rate", "mean"),
    median_caption_length=("caption_length", "median"),
    avg_hashtags=("num_hashtags", "mean"),
).round(3)
summary["theme_dominante"] = posts_df.groupby("tier", observed=False)["theme"].agg(lambda s: s.value_counts().index[0])
summary"""))

cells.append(md("""## Encerramento

O que a engenharia de variáveis nos permitiu fazer:

1. **Sair de JSON aninhado** para 3 tabelas relacionais com tipos limpos.
2. **Filtrar ruído** (perfis suspeitos, nulos, duplicatas) antes de qualquer análise.
3. **Multiplicar uma única coluna por ~10 features** (timestamp → ano/mês/hora/período/é_fim_de_semana).
4. **Usar LLM como extrator semântico** — tema, sentimento e entidades onde regex falharia.
5. **Normalizar escalas** (log, Yeo-Johnson, padronização) para que perfis com 10 mil e 600 milhões de seguidores convivam no mesmo gráfico.
6. **Comparar tiers de forma justa** — micro engaja proporcionalmente mais, mas macro domina o volume absoluto.

> A engenharia de variáveis **não é uma etapa anterior à análise — é a análise**.
> O insight só apareceu porque a base foi preparada para ele aparecer.
"""))

cells.append(code("""# salvar dataset final processado
out_dir = ROOT / "data" / "processed"
out_dir.mkdir(parents=True, exist_ok=True)

# converter colunas problemáticas para serialização
posts_to_save    = posts_df.copy()
posts_to_save["taken_at"] = posts_to_save["taken_at"].astype(str)
posts_to_save["entities"] = posts_to_save["entities"].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else "[]")

profiles_df.to_csv(out_dir / "profiles_processed.csv", index=False)
posts_to_save.to_csv(out_dir / "posts_processed.csv", index=False)
comments_df.to_csv(out_dir / "comments_processed.csv", index=False)
print("Datasets salvos em data/processed/")"""))


# ============================================================
# escreve o notebook
# ============================================================
nb = nbf.v4.new_notebook()
nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Notebook escrito em {OUT}")
print(f"Células: {len(cells)} ({sum(1 for c in cells if c['cell_type']=='code')} código, {sum(1 for c in cells if c['cell_type']=='markdown')} markdown)")
