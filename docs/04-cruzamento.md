# 04 — Cruzamento de variáveis

## Slide 1: O que é
- Criar **features novas combinando** as existentes.
- Dois sabores:
  - **Numérico** (feature crossing): operações entre colunas (`A/B`, `A*B`).
  - **Categórico**: pares de categorias (`tier × theme`) para análise multidimensional.
- O cruzamento revela **interações** que cada feature isolada não mostra.

## Slide 2: Cuidados
- Cruzar tudo com tudo gera explosão combinatória — escolher pares com **hipótese clara**.
- Dividir por zero é um clássico: `engagement_rate = likes / followers` precisa proteger followers=0.
- Cruzamentos categóricos geram tabelas esparsas — agregar antes de visualizar.

## Slide 3: O que fizemos no projeto
- **`engagement_rate = (likes + comments) / followers`** — normaliza para comparação entre tiers.
- **`comments_per_like = comments / likes`** — sinaliza posts polêmicos/discutidos.
- **`tier × theme`** (heatmap) — mostra que macro fala mais de "lifestyle/promocional", micro fala mais de "educacional".
- **`period_of_day × engagement_quartile`** — revela em que períodos os virais concentram.

## Notas do apresentador
> "Likes absolutos é uma métrica de vaidade — Cristiano sempre vence. Mas
> `engagement_rate` é uma métrica de qualidade. Quando a gente cria essa feature
> cruzando duas existentes, o ranking *muda completamente*. Esse é o ponto:
> a feature certa muda a história que os dados contam."

**Transição:** depois de cruzar, precisamos colocar tudo na mesma escala — Seção 7.
