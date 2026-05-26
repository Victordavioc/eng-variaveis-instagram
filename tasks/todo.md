# tasks/todo.md: Engenharia de Variáveis com Instagram

## Status geral
- [x] Validar endpoints Hiker (perfil, mídias, comentários) e Gemini
- [x] Criar estrutura do projeto (pastas, `.env.example`, `.gitignore`, `requirements.txt`)
- [x] Implementar `src/hiker_client.py` (cache em disco + paginação + retry)
- [x] Implementar `src/gemini_client.py` (cache por hash + retry)
- [x] Implementar `src/data_loader.py` (json_normalize → 3 DataFrames)
- [x] Coletar dados (~16 perfis válidos, ~385 posts, ~657 comentários)
- [x] Construir `notebooks/apresentacao.ipynb` (9 seções, ~49 células)
- [x] Gerar `README.md` e arquivos em `tasks/`
- [x] Gerar `docs/*.md` (9 arquivos: 7 conceitos + conclusão + questionário)
- [x] Executar o notebook de ponta a ponta sem erro

## Revisão final

### O que foi entregue
- Notebook didático em português, ~45 min de apresentação.
- 6 técnicas de engenharia de variáveis + 1 capítulo extra sobre LLM.
- 4 perguntas analíticas respondidas com gráficos no final.
- Roteiros de slides (`docs/`) e questionário com 10 questões.
- Cache em disco para Hiker e Gemini. Re-execução é gratuita.

### Decisões de design
- **Notebook gerado via script** (`scripts/build_notebook.py`): mais fácil de regenerar e auditar do que editar `.ipynb` à mão.
- **3 perfis com problema na coleta** (privado / inexistente / novo) foram mantidos como exemplo natural de "exclusão de anomalias" na Seção 2.
- **LLM em batches** (~25 inputs por prompt): reduz nº de chamadas em ~25× sem perder qualidade.
- **`gemini-3-flash-preview`** como default: mais novo e barato, com quota gratuita generosa.

### Riscos remanescentes
- Cota do Gemini free tier pode expirar; nesse caso o pipeline cai no fallback determinístico (regex/lexicon) automaticamente. Trocar `GEMINI_MODEL` no `.env` para `gemini-2.5-flash-lite` pode ajudar a re-aquecer o cache.
- Hiker pode mudar schema dos endpoints. O `data_loader` foi escrito de forma resiliente (usa `.get()` e fallback para colunas ausentes).

### Insights numéricos produzidos pelo notebook (cache atual)
- **16 perfis válidos**, 385 posts, 657 comentários após limpeza.
- **micro engaja 70% mais que macro:** engagement_rate médio 0.019 (micro) vs 0.011 (macro).
- **Sentimento:** 55% positivo no macro vs 33% no micro. Fanbase grande comenta mais positivo.
- **Tema dominante:** `promocional` (93 posts), seguido de `educacional` (71). Sinal de mix entre macro patrocinado e micro tech educacional.
- **Pipeline LLM:** 14 batches via LLM para temas (100% cobertura), 7+7 para entidades (50% LLM / 50% fallback), 0+25 para sentimento (100% fallback por quota esgotada; pipeline continuou funcionando).
