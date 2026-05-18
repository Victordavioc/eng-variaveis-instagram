"""Carrega JSONs cacheados em data/raw/ e produz 3 DataFrames relacionais.

- profiles_df: 1 linha por perfil
- posts_df:    1 linha por post (FK user_pk)
- comments_df: 1 linha por comentário (FK media_pk)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def _read_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def load_profiles(raw_dir: Path | None = None) -> pd.DataFrame:
    raw_dir = raw_dir or RAW_DIR
    profile_dir = raw_dir / "profile"
    if not profile_dir.exists():
        return pd.DataFrame()
    rows = []
    for p in sorted(profile_dir.glob("*.json")):
        body = _read_json(p)
        if not isinstance(body, dict):
            continue
        rows.append(body)
    if not rows:
        return pd.DataFrame()
    df = pd.json_normalize(rows)
    # garantir tipos
    if "pk" in df.columns:
        df["pk"] = df["pk"].astype(str)
    return df


def load_posts(raw_dir: Path | None = None) -> pd.DataFrame:
    raw_dir = raw_dir or RAW_DIR
    medias_dir = raw_dir / "medias"
    if not medias_dir.exists():
        return pd.DataFrame()
    rows = []
    for p in sorted(medias_dir.glob("*.json")):
        body = _read_json(p)
        if not isinstance(body, list) or not body:
            continue
        page = body[0] if isinstance(body[0], list) else []
        rows.extend(page)
    if not rows:
        return pd.DataFrame()
    df = pd.json_normalize(rows)
    # FK explícito
    if "user.pk" in df.columns:
        df["user_pk"] = df["user.pk"].astype(str)
    if "pk" in df.columns:
        df["media_pk"] = df["pk"].astype(str)
    return df


def load_comments(raw_dir: Path | None = None) -> pd.DataFrame:
    raw_dir = raw_dir or RAW_DIR
    comments_dir = raw_dir / "comments"
    if not comments_dir.exists():
        return pd.DataFrame()
    rows = []
    for p in sorted(comments_dir.glob("*.json")):
        # nome do arquivo: <media_pk>_p<page>.json
        media_pk = p.stem.split("_p")[0]
        body = _read_json(p)
        if not isinstance(body, list) or not body:
            continue
        page = body[0] if isinstance(body[0], list) else []
        for c in page:
            if isinstance(c, dict):
                c2 = dict(c)
                c2["media_pk"] = str(media_pk)
                rows.append(c2)
    if not rows:
        return pd.DataFrame()
    df = pd.json_normalize(rows)
    if "pk" in df.columns:
        df["comment_pk"] = df["pk"].astype(str)
    return df


def load_all(raw_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return load_profiles(raw_dir), load_posts(raw_dir), load_comments(raw_dir)
