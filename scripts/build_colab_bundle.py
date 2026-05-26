"""Gera colab-bundle.zip contendo tudo necessário para rodar o notebook no Colab.

Estrutura do zip:
  apresentacao.ipynb       (com célula de bootstrap injetada no topo)
  README-colab.md          (instruções de uso)
  requirements.txt
  src/                     (módulos importados pelo notebook)
  data/raw/                (JSONs cacheados da Hiker, ~11 MB)
  data/processed/llm_cache.json  (44 KB, cache do LLM)
"""
from __future__ import annotations

import copy
import json
import shutil
import zipfile
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
NB_SRC = ROOT / "notebooks" / "apresentacao.ipynb"
OUT_ZIP = ROOT / "colab-bundle.zip"

BOOTSTRAP_MD = """\
## Setup do Colab (rode esta seção uma vez)

Antes de executar o notebook:

1. **Suba este arquivo** (`colab-bundle.zip`) na aba *Files* (ícone de pasta à esquerda).
2. **Cadastre as chaves de API** em *Secrets* (ícone de chave 🔑):
   - `HIKER_API_KEY`
   - `GEMINI_API_KEY`
   - Marque *Notebook access* em ambas.
3. **Execute a célula abaixo**. Ela descompacta o zip, instala dependências e exporta as chaves.
"""

BOOTSTRAP_CODE = """\
# Bootstrap do Colab (idempotente: rodar várias vezes não quebra nada)
import os, sys, subprocess
from pathlib import Path

# 1. Descompacta o bundle se ainda não foi
if not Path("/content/src").exists():
    print("Descompactando colab-bundle.zip ...")
    subprocess.run(["unzip", "-o", "-q", "/content/colab-bundle.zip", "-d", "/content/"], check=True)
    print("OK.")

# 2. Instala google-genai (não vem por padrão no Colab; demais libs já estão)
try:
    import google.genai  # noqa: F401
except ImportError:
    print("Instalando google-genai ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai", "python-dotenv"], check=True)

# 3. Pega as chaves do Secrets do Colab e exporta como env vars
try:
    from google.colab import userdata
    os.environ["HIKER_API_KEY"]  = userdata.get("HIKER_API_KEY")
    os.environ["GEMINI_API_KEY"] = userdata.get("GEMINI_API_KEY")
except Exception as e:
    print(f"[aviso] não consegui ler Secrets do Colab: {e}")
    print("       defina HIKER_API_KEY e GEMINI_API_KEY manualmente via os.environ[...] = ...")

os.environ.setdefault("GEMINI_MODEL", "gemini-2.5-flash")

# 4. Garante que ROOT do projeto é /content (no Colab)
os.chdir("/content")
print("Setup pronto. Rode a célula seguinte (Seção 1) para começar.")
"""


def inject_bootstrap(nb_path: Path) -> dict:
    """Retorna um notebook dict com 2 células (markdown + code) injetadas no topo."""
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)
    bootstrap_cells = [
        nbf.v4.new_markdown_cell(BOOTSTRAP_MD),
        nbf.v4.new_code_cell(BOOTSTRAP_CODE),
    ]
    nb["cells"] = bootstrap_cells + nb["cells"]
    return nb


def write_readme(p: Path) -> None:
    p.write_text(
        """# Como rodar no Google Colab

1. Crie um *novo notebook* no Colab → arraste **este zip** para o painel *Files* (ícone de pasta).
2. Abra `apresentacao.ipynb` (que está dentro do zip; primeiro descompacte usando a célula de bootstrap dele).

## Passo a passo curto

a. Crie um Colab vazio.
b. Faça upload de `colab-bundle.zip` na barra lateral de arquivos.
c. Em *Secrets* (ícone de chave), cadastre `HIKER_API_KEY` e `GEMINI_API_KEY`.
d. Cole esta única linha numa célula e rode:
   ```python
   !unzip -o colab-bundle.zip && jupyter notebook --version
   ```
e. Abra `/content/apresentacao.ipynb` pelo painel de arquivos.
f. Rode todas as células (*Runtime → Run all*).

## O que cada coisa faz
- `apresentacao.ipynb`: notebook com célula de bootstrap injetada que faz unzip + instala libs + lê Secrets.
- `src/`: wrappers Hiker e Gemini com cache, e o data loader.
- `data/raw/`: JSONs já coletados da Hiker. Sem isso, o notebook não tem dados para processar.
- `data/processed/llm_cache.json`: cache do LLM com 21 batches já processados (themes + entities). Sem ele, Seção 4 cai 100% no fallback determinístico.

## Notas
- Não inclua o `.env` aqui. Use *Colab Secrets*, é mais seguro.
- O bundle tem ~11 MB no total (data/raw é o maior pedaço).
- Re-executar o notebook não consome créditos de API (tudo em cache).
""",
        encoding="utf-8",
    )


def main() -> None:
    # 1. notebook com bootstrap
    nb = inject_bootstrap(NB_SRC)
    tmp_nb = ROOT / "_tmp_apresentacao_colab.ipynb"
    with open(tmp_nb, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    # 2. README específico do Colab
    tmp_readme = ROOT / "_tmp_README-colab.md"
    write_readme(tmp_readme)

    # 3. listar arquivos a incluir
    files: list[tuple[Path, str]] = []  # (src_abs, arcname)
    files.append((tmp_nb, "apresentacao.ipynb"))
    files.append((tmp_readme, "README-colab.md"))
    files.append((ROOT / "requirements.txt", "requirements.txt"))

    # src/ (sem __pycache__)
    for p in (ROOT / "src").iterdir():
        if p.is_file() and p.suffix == ".py":
            files.append((p, f"src/{p.name}"))

    # scripts/: necessários se o usuário quiser refazer coleta/cache/notebook no Colab
    for p in (ROOT / "scripts").iterdir():
        if p.is_file() and p.suffix == ".py":
            files.append((p, f"scripts/{p.name}"))

    # data/raw/**/*.json
    for p in (ROOT / "data" / "raw").rglob("*.json"):
        rel = p.relative_to(ROOT).as_posix()
        files.append((p, rel))

    # data/processed/llm_cache.json
    cache_p = ROOT / "data" / "processed" / "llm_cache.json"
    if cache_p.exists():
        files.append((cache_p, "data/processed/llm_cache.json"))

    # 4. zip
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for src, arc in files:
            zf.write(src, arc)

    # 5. limpar temporários
    tmp_nb.unlink()
    tmp_readme.unlink()

    size_mb = OUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Bundle criado: {OUT_ZIP}")
    print(f"Tamanho: {size_mb:.2f} MB")
    print(f"Arquivos incluídos: {len(files)}")


if __name__ == "__main__":
    main()
