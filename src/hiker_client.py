"""Wrapper da Hiker API com cache em disco.

Cada chamada cacheia o JSON bruto em data/raw/<endpoint>/<chave>.json.
Re-rodar o pipeline não consome créditos novamente.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.hikerapi.com"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


class HikerClient:
    def __init__(self, api_key: str | None = None, raw_dir: Path | None = None, sleep_s: float = 0.3,
                 force_refresh: bool | set[str] = False):
        """
        force_refresh:
          False        usa cache normalmente (default)
          True         ignora cache de todos os buckets e re-baixa tudo
          {"profile"}  ignora cache apenas dos buckets listados
                       (valores válidos: "profile", "medias", "comments")
        """
        self.api_key = api_key or os.getenv("HIKER_API_KEY")
        if not self.api_key:
            raise RuntimeError("HIKER_API_KEY não definida. Crie um .env a partir de .env.example.")
        self.raw_dir = Path(raw_dir) if raw_dir else RAW_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.sleep_s = sleep_s  # pausa pequena entre chamadas para ser respeitoso
        self.force_refresh = force_refresh

    # ---------- baixo nível ----------
    def _cache_path(self, bucket: str, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-._" else "_" for c in key)
        d = self.raw_dir / bucket
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{safe}.json"

    def _cache_invalidated(self, bucket: str) -> bool:
        if self.force_refresh is True:
            return True
        if isinstance(self.force_refresh, (set, frozenset, list, tuple)):
            return bucket in self.force_refresh
        return False

    def _get(self, path: str, params: dict[str, Any], bucket: str, key: str,
             max_retries: int = 4) -> Any:
        cache = self._cache_path(bucket, key)
        if cache.exists() and not self._cache_invalidated(bucket):
            with open(cache, "r", encoding="utf-8") as f:
                return json.load(f)

        url = f"{BASE_URL}{path}"
        headers = {"x-access-key": self.api_key, "accept": "application/json"}

        backoff = 1.0
        for attempt in range(max_retries):
            try:
                r = requests.get(url, params=params, headers=headers, timeout=30)
                if r.status_code == 200:
                    body = r.json()
                    with open(cache, "w", encoding="utf-8") as f:
                        json.dump(body, f, ensure_ascii=False)
                    time.sleep(self.sleep_s)
                    return body
                if r.status_code in (429, 502, 503, 504):
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                # erro definitivo: salva placeholder vazio para não re-tentar
                print(f"[hiker] {path} {params} -> {r.status_code}: {r.text[:200]}")
                return None
            except requests.RequestException as e:
                print(f"[hiker] exceção {e} tentativa {attempt+1}")
                time.sleep(backoff)
                backoff *= 2
        return None

    # ---------- endpoints de alto nível ----------
    def user_by_username(self, username: str) -> dict | None:
        return self._get(
            "/v1/user/by/username",
            {"username": username},
            bucket="profile",
            key=username,
        )

    def user_medias(self, user_id: str | int, max_pages: int = 2) -> list[dict]:
        """Retorna lista plana de medias paginadas. Cada página é cacheada separadamente."""
        medias: list[dict] = []
        max_id: str | None = None
        for page in range(max_pages):
            params: dict[str, Any] = {"user_id": str(user_id)}
            if max_id:
                params["end_cursor"] = max_id
            key = f"{user_id}_p{page}"
            body = self._get("/v1/user/medias/chunk", params, bucket="medias", key=key)
            if not body or not isinstance(body, list):
                break
            page_medias = body[0] if isinstance(body[0], list) else []
            medias.extend(page_medias)
            next_cursor = body[1] if len(body) > 1 else None
            if not next_cursor:
                break
            max_id = next_cursor
        return medias

    def media_comments(self, media_id: str | int, max_pages: int = 2) -> list[dict]:
        """Retorna lista plana de comentários paginados."""
        comments: list[dict] = []
        max_id: str | None = None
        for page in range(max_pages):
            params: dict[str, Any] = {"id": str(media_id)}
            if max_id:
                params["min_id"] = max_id
            key = f"{media_id}_p{page}"
            body = self._get("/v1/media/comments/chunk", params, bucket="comments", key=key)
            if not body or not isinstance(body, list):
                break
            page_comments = body[0] if isinstance(body[0], list) else []
            comments.extend(page_comments)
            next_cursor = body[1] if len(body) > 1 else None
            if not next_cursor:
                break
            max_id = next_cursor
        return comments
