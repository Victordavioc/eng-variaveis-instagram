# 02: Discretização

## Slide 1: O que é
- Transformar variável **contínua** em **categórica ordenada**.
- Permite agrupar, comparar e visualizar sem dominância dos extremos.
- Duas abordagens:
  - `pd.cut`: **bins fixos** (decisão do domínio: "<100k é micro").
  - `pd.qcut`: **bins por quantis** (decisão dos dados: "os 25% mais baixos").

## Slide 2: Quando usar / cuidados
- Use `cut` quando há **convenção de domínio** (faixas etárias, tiers de influenciador).
- Use `qcut` quando quer **distribuição balanceada** entre as categorias.
- **Cuidado com perda de informação:** discretizar demais apaga nuances.
- Sempre escolher *labels significativos*. "baixo/médio/alto" diz mais que "1/2/3".

## Slide 3: O que fizemos no projeto
- `follower_count` → `tier` ∈ {micro <100k, mid 100k-1M, macro >1M} via `pd.cut`.
- `like_count` → `engagement_quartile` ∈ {baixo, médio, alto, viral} via `pd.qcut`.
- `caption_length` → `caption_band` ∈ {curta <50, média 50-200, longa >200} via `pd.cut`.
- `hour` → `period_of_day` ∈ {madrugada, manhã, tarde, noite} via função.
- **Resultado:** `tier` é a variável-chave que viabiliza a comparação justa entre micro/mid/macro nas seções seguintes.

## Notas do apresentador
> "Se a gente comparasse 'média de likes' direto entre Cristiano e o lucasmontano,
> Cristiano ganha de longe. Mas quando a gente cria a feature `tier` e compara
> *dentro* do tier, descobre que o micro tem `engagement_rate` proporcionalmente
> *maior*: a audiência menor é mais engajada. Esse insight só existe porque
> discretizamos."

**Transição:** depois de discretizar, podemos *cruzar* categorias na Seção 6.
