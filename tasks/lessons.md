# tasks/lessons.md: Lições aprendidas

> Lições capturadas durante o desenvolvimento deste projeto. Servem para reduzir a
> taxa de erro em projetos futuros similares.

## 2026-05-18: Sempre validar API com 1 request mínimo antes do orçamento

**Padrão observado:** o documento original especificava o parâmetro `media_id` para o
endpoint `/v1/media/comments/chunk`, mas o nome real era `id`. Um único request de
validação prévio evitou paginação repetida com erro 422 em produção.

**Regra:** antes de rodar coleta em lote, fazer 1 chamada exploratória em cada endpoint
para confirmar parâmetros e schema de resposta.

## 2026-05-18: Cache em disco antes de qualquer chamada paga

**Padrão observado:** Hiker e Gemini cobram por chamada. Sem cache, re-executar o
notebook custaria várias vezes o preço da primeira coleta.

**Regra:** todo wrapper de API paga deve ter cache em disco *desde a primeira versão*,
não como "feature futura". `data/raw/<endpoint>/<chave>.json` para JSONs grandes;
hash de prompt para chamadas LLM.

## 2026-05-18: Free tier do Gemini varia por modelo

**Padrão observado:** `gemini-2.0-flash` teve quota zero no projeto da chave, mas
`gemini-2.5-flash-lite`, `gemini-2.5-flash` e `gemini-3-flash-preview` funcionaram.

**Regra:** se a primeira chamada falhar com `RESOURCE_EXHAUSTED`, testar 3-4 modelos
alternativos antes de declarar a chave morta. Modelos `*-lite` e `*-preview`
frequentemente têm tier gratuito mais permissivo.

## 2026-05-18: Sempre desenhar fallback determinístico para features dependentes de LLM

**Padrão observado:** durante a execução do notebook, o free tier do Gemini esgotou a
quota daily no meio da classificação de sentimento. Sem fallback, ~50% das features
viraram "neutro" default e a análise perdeu valor. Com fallback (lexicon-based),
a coluna `sentiment_source` deixa transparente que a feature veio do plano B.

**Regra:** toda feature derivada de LLM deve ter:
1. Função `*_via_llm()` que retorna `None` em falha (não dispara exceção).
2. Função `*_fallback()` determinística (regex/lexicon).
3. Coluna `*_source` no DataFrame indicando a origem.

Pipeline assim **nunca falha por causa de dependência externa** e o usuário sabe
exatamente em quais linhas o LLM agregou valor.

## 2026-05-18: fail_fast em 429 economiza minutos de backoff

**Padrão observado:** retry com backoff exponencial (2,4,8,16,32s) em cima de 429 do
free tier que está esgotado *não recupera nada*; só desperdiça 60+ segundos por
chamada antes do fallback assumir.

**Regra:** quando um endpoint retorna 429 com hint de retry maior que 30s, é quota
diária esgotada. Falhar imediatamente e cair no fallback é melhor do que retentar.
Adicionar flag `fail_fast_on_quota=True` no wrapper.

## 2026-05-18: Gerar notebook via script (não editar JSON à mão)

**Padrão observado:** notebooks Jupyter são JSON com escaping complicado. Editar
diretamente é frágil; qualquer aspas mal escapada quebra tudo.

**Regra:** sempre que o notebook for >5 células, manter o conteúdo em um script
Python que monta as células via `nbformat.v4.new_*_cell()` e serializa. Auditar e
regenerar fica trivial.
