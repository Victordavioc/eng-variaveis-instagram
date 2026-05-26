# 06: Transformações não-lineares

## Slide 1: O que é
- Aplicar **funções não-lineares** (`log`, `sqrt`, `Box-Cox`, `Yeo-Johnson`) que mudam a *forma* da distribuição.
- Objetivo: **aproximar de uma normal** ou pelo menos comprimir caudas longas.
- Diferente da padronização linear: aqui a *forma* muda.

## Slide 2: Quando usar / cuidados
- **log/log1p:** dados positivos com cauda longa (likes, followers, views, salários, preços).
- **sqrt:** caudas moderadas, contagens (ex: número de comentários).
- **Box-Cox:** generalização do log, mas exige `x > 0`.
- **Yeo-Johnson:** generalização de Box-Cox que **aceita zero e negativos**. Mais robusta.
- **Cuidado com zeros:** `log(0)` é -∞. Use `log1p(x) = log(1+x)` por segurança.
- A transformação pode **inverter** a interpretação de coeficientes. Sempre documentar.

## Slide 3: O que fizemos no projeto
- `log1p(like_count)`, `log1p(comment_count)`, `log1p(follower_count)`: todas com cauda longa clássica de redes sociais.
- `PowerTransformer(method="yeo-johnson")` em `engagement_rate`: lida com zeros (quando um post não teve engajamento).
- **Resultado:** o histograma de likes passa de "tudo empilhado em 0 com 1-2 barras minúsculas no canto" para uma distribuição quase log-normal, **com a cauda visualmente comprimida**.
- É o que viabiliza o scatter `engagement_rate × follower_count` no slide final. Sem `log`, micro influenciadores ficavam todos colados no eixo Y.

## Notas do apresentador
> "Olha o gráfico antes do log: você só enxerga Cristiano. Depois do log: você
> enxerga todos os 16 perfis. Nenhuma técnica de visualização ou modelo iria
> ajudar. A única coisa que ajuda é a transformação não-linear. Esse é
> provavelmente o passo mais subestimado em data science."

**Pergunta provável:** "Por que log1p e não log?"
**Resposta:** porque o dataset tem posts com 0 comentários. `log(0)` é
indefinido; `log1p(0) = 0`. É um detalhe pequeno mas crucial para não perder linhas.
