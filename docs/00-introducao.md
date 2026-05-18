# 00 — Introdução: por que Instagram?

## Slide 1: O problema
- Dados de redes sociais chegam como **JSON aninhado**, com campos compostos, texto livre e métricas em escalas enormes.
- Antes de qualquer análise, é preciso **transformar essa lama em colunas de DataFrame**.
- Esse é o domínio da **Engenharia de Variáveis**.

## Slide 2: Por que esse dataset é didático
- **Escalas absurdas:** Cristiano (660M followers) ao lado de micro (10k) — força a usar log.
- **Texto livre:** captions e comentários — força features semânticas e LLM.
- **Datas em timestamp:** força decomposição em ano/mês/hora/período.
- **Categorias ricas:** tipo de mídia, verificação, business account — força discretização e cruzamento.

## Slide 3: As 4 perguntas analíticas
Cada técnica que vamos cobrir está a serviço de responder:

1. **Saúde do perfil** — quem tem engajamento suspeito?
2. **Caption analysis** — o que caracteriza captions de alto desempenho?
3. **Comportamento da audiência** — o que os comentários revelam?
4. **Comparação entre tiers** — micro × mid × macro.

## Notas do apresentador
> "A engenharia de variáveis não é uma etapa que vem antes da análise. É a análise.
> Sem features bem construídas, qualquer modelo ou gráfico é ruído. Hoje vamos mostrar,
> com um dataset real do Instagram, como cada técnica conecta com uma pergunta concreta."

**Transição:** apresentar o schema cru da Hiker API (mostrar um JSON aninhado de
perfil) → "olha o tamanho disso. Vamos aprender a achatar e domar."
