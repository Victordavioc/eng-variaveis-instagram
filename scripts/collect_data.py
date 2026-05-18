"""Script de coleta. Roda uma vez, salva tudo no cache em data/raw/.
Re-rodar é idempotente e gratuito.
"""
from __future__ import annotations

import sys
from pathlib import Path

# permite rodar como script direto
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from src.hiker_client import HikerClient

load_dotenv(ROOT / ".env")

USERNAMES = [
    # macro (>1M)
    "cristiano", "leomessi", "kyliejenner", "natgeo", "nasa", "nike",
    "chrishemsworth", "bts.bighitofficial", "garyvee", "mkbhd",
    # mid (100k-1M, mix de nichos BR tech/criadores)
    "filipedeschamps", "rocketseat",
    # micro (10k-100k)
    "diolinha", "lucasmontano", "rafaballerini", "attainablefitness",
    "programadornaoborn", "cursoemvideo",
]

# parâmetros conservadores: 2 páginas de mídias (~24 posts), 1 página de comentários (~12 cmts)
MEDIA_PAGES = 2
TOP_K_POSTS_FOR_COMMENTS = 3
COMMENT_PAGES = 1


def main() -> None:
    client = HikerClient()
    summary = []
    for username in USERNAMES:
        print(f"\n=== {username} ===")
        profile = client.user_by_username(username)
        if not profile or "pk" not in profile:
            print(f"  perfil indisponível, pulando")
            summary.append((username, 0, 0))
            continue
        user_id = profile["pk"]
        print(f"  pk={user_id} followers={profile.get('follower_count')}")
        medias = client.user_medias(user_id, max_pages=MEDIA_PAGES)
        print(f"  {len(medias)} mídias coletadas")

        # top K por like_count para comentários
        ranked = sorted(
            [m for m in medias if isinstance(m, dict) and m.get("like_count") is not None],
            key=lambda m: m.get("like_count", 0),
            reverse=True,
        )[:TOP_K_POSTS_FOR_COMMENTS]
        cmt_total = 0
        for m in ranked:
            mpk = m.get("pk") or m.get("id")
            if not mpk:
                continue
            cs = client.media_comments(mpk, max_pages=COMMENT_PAGES)
            cmt_total += len(cs)
            print(f"    media {mpk[:18]}… likes={m.get('like_count')} -> {len(cs)} comentários")
        summary.append((username, len(medias), cmt_total))

    print("\n=== resumo ===")
    for u, p, c in summary:
        print(f"  {u:30s} posts={p:>4} comments={c:>4}")


if __name__ == "__main__":
    main()
