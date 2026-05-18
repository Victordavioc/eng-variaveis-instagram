"""Wrapper Gemini com cache em disco.

Toda chamada é chaveada por hash(model + prompt). Re-rodar não chama LLM de novo.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "llm_cache.json"


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None,
                 cache_path: Path | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY não definida. Crie um .env a partir de .env.example.")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        self.cache_path = Path(cache_path) if cache_path else CACHE_PATH
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache = self._load_cache()
        self._client = None  # lazy

    def _load_cache(self) -> dict[str, Any]:
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self) -> None:
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def _ensure_client(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @staticmethod
    def _hash_key(model: str, prompt: str) -> str:
        h = hashlib.sha256()
        h.update(model.encode("utf-8"))
        h.update(b"\x00")
        h.update(prompt.encode("utf-8"))
        return h.hexdigest()[:16]

    # se True, no primeiro 429 já fail-fast (não retenta).
    # Útil quando a daily quota está esgotada e queremos cair no fallback rapidamente.
    fail_fast_on_quota: bool = True

    def generate_json(self, prompt: str, temperature: float = 0.0,
                      max_retries: int = 2) -> Any:
        """Envia prompt ao Gemini, exige resposta JSON, devolve objeto Python.

        Em falha (incluindo rate-limit), devolve None e o caller deve aplicar fallback.
        Para evitar travar minutos em backoff, fail-fast em 429 por padrão.
        """
        key = self._hash_key(self.model, prompt)
        if key in self._cache:
            return self._cache[key]

        from google.genai import types
        client = self._ensure_client()

        backoff = 2.0
        for attempt in range(max_retries):
            try:
                resp = client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=temperature,
                    ),
                )
                text = (resp.text or "").strip()
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    start = text.find("{")
                    end = text.rfind("}")
                    if start >= 0 and end > start:
                        parsed = json.loads(text[start:end+1])
                    else:
                        parsed = None
                self._cache[key] = parsed
                self._save_cache()
                return parsed
            except Exception as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    if self.fail_fast_on_quota:
                        # quota esgotada — caller deve usar fallback
                        break
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                if "503" in msg or "UNAVAILABLE" in msg:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                print(f"[gemini] erro {msg[:200]}")
                break
        # não cacheia None para permitir retry futuro quando a quota voltar
        return None
