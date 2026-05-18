# 03 — Decomposição

## Slide 1: O que é
- Quebrar um campo composto em **várias features primitivas**.
- Mais informativo do que manter um campo "monolítico" que esconde várias dimensões.
- Casos clássicos:
  - **Timestamp** → ano, mês, dia, hora, dia da semana, período, é fim de semana.
  - **Endereço** → cidade, estado, CEP, país.
  - **Texto livre** → comprimento, contagem de hashtags, mentions, emojis, idioma.

## Slide 2: Cuidados
- Não decompor demais: features extremamente granulares (segundo do post) raramente agregam.
- Manter o **campo original** caso precise revisitar — decomposição é aditiva.
- Tipagem correta importa: `weekday` como string ordenada, não inteiro arbitrário.

## Slide 3: O que fizemos no projeto
- `taken_at` (ISO 8601) → 7 features: ano, mês, dia, hora, dia da semana, período do dia, é fim de semana.
- `caption_text` → 6 features: comprimento, num_hashtags, num_mentions, num_emojis, num_linhas, has_caption.
- **Resultado:** uma única coluna virou **13 features novas**. Cada uma pode entrar em correlações, gráficos, modelos.
- Os gráficos de "posts por dia da semana" e "posts por período" só existem por causa dessa decomposição.

## Notas do apresentador
> "A Hiker me deu uma string `2026-05-15T19:22:45Z`. Sozinha, ela não responde
> nenhuma pergunta. Mas quando eu decomponho em hora=19 e period_of_day='noite',
> de repente eu posso responder: 'qual o período em que os virais mais aparecem?'
> A informação estava lá o tempo todo — só estava enrolada."

**Pergunta provável:** "Por que não usaram o timestamp UNIX direto?"
**Resposta:** ele é uma feature *aditiva* (continua no DataFrame), mas não é
interpretável. Decomposição não substitui o campo original; ela acrescenta dimensões.
