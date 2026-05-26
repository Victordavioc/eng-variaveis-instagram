# Engenharia de Variáveis com Dados do Instagram

Trabalho da disciplina **Engenharia de Variáveis** (UFG). Constrói uma base de dados a
partir de JSONs semi-estruturados do Instagram (via [Hiker API](https://hikerapi.com/)),
demonstrando as 6 técnicas fundamentais de engenharia de variáveis:

1. Exclusão de anomalias
2. Decomposição
3. Cruzamento
4. Discretização
5. Transformações lineares
6. Transformações não-lineares

…mais um capítulo extra sobre **features semânticas via LLM (Gemini)**, que é
a forma moderna de engenharia de features sobre texto não-estruturado.

## Estrutura

```
├── .env.example               # template das chaves
├── requirements.txt
├── data/
│   ├── raw/                   # JSONs brutos da Hiker (cacheados)
│   └── processed/             # dataset final + cache do LLM
├── notebooks/
│   └── apresentacao.ipynb     # entregável principal (45 min de apresentação)
├── src/
│   ├── hiker_client.py        # wrapper Hiker com cache em disco
│   ├── gemini_client.py       # wrapper Gemini com cache em disco
│   └── data_loader.py         # JSON → 3 DataFrames relacionais
├── scripts/
│   ├── collect_data.py        # coleta inicial (idempotente; usa cache)
│   └── build_notebook.py      # regenera o notebook a partir do código fonte
└── docs/                      # roteiros de slides + questionário
```

## Como rodar

```powershell
# 1. crie o ambiente e instale dependências
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. configure as chaves
copy .env.example .env
# (edite .env preenchendo HIKER_API_KEY e GEMINI_API_KEY)

# 3. colete os dados (idempotente: só baixa o que ainda não está em data/raw/)
python scripts/collect_data.py

# 4. (opcional) regenere o notebook a partir do script fonte
python scripts/build_notebook.py

# 5. abra o notebook
jupyter notebook notebooks/apresentacao.ipynb
```

> Com **cache quente** (todas as chamadas já feitas), o notebook executa em **< 2 minutos**.
> Em cache frio, a primeira execução leva ~10 a 15 min (chamadas LLM + Hiker).

## Reprodutibilidade

- **Hiker:** cada response é salvo em `data/raw/<endpoint>/<chave>.json`.
- **Gemini:** cada prompt é chaveado por `sha256(model + prompt)` e cacheado em
  `data/processed/llm_cache.json`.
- Re-executar qualquer parte **não consome créditos** enquanto o cache existir.

## Segurança

- `.env` está no `.gitignore` (a chave **nunca** vai pro repositório).
- Todos os módulos lêem chaves via `os.getenv()`. Nada hardcoded.
- Use `.env.example` como template para colaboradores.

## Stack

Python 3.10+, pandas, numpy, scikit-learn, matplotlib, seaborn, requests,
[`google-genai`](https://github.com/googleapis/python-genai) (SDK oficial do Gemini),
python-dotenv.
