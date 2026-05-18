# 05 — Transformações lineares

## Slide 1: O que é
- Aplicar **transformação afim** `x' = a·x + b` para reescalar variáveis.
- Não muda a *forma* da distribuição, só a escala/centralização.
- Duas formas canônicas:
  - **StandardScaler** (`z-score`): média 0, desvio 1.
  - **MinMaxScaler**: escala [0, 1].

## Slide 2: Quando usar / cuidados
- Use **StandardScaler** quando há suposição de normalidade (PCA, regressão).
- Use **MinMaxScaler** quando precisa de range fixo (radar charts, redes neurais, similaridade).
- **Sensível a outliers:** um único valor extremo desloca toda a escala. Considere `RobustScaler` se houver outliers fortes.
- Sempre fitar no treino e transformar no teste (em ML); aqui é análise descritiva então não tem essa separação.

## Slide 3: O que fizemos no projeto
- Aplicamos `StandardScaler` em `like_count`, `comment_count`, `caption_length`, `engagement_rate`, `num_hashtags`.
- Cada feature virou também `<feature>_std` e `<feature>_mm` (Min-Max), preservando o original.
- **Resultado visual:** o histograma de `like_count` pré-padronização tem cauda gigante (Cristiano domina). Pós-padronização, vira z-score — mas a *forma* da distribuição continua a mesma. Padronização linear não resolve cauda longa, só centra.

## Notas do apresentador
> "Padronização linear é como mudar de Celsius para Fahrenheit — os valores mudam,
> mas o que era extremo continua extremo. Para domar a cauda longa do Instagram,
> a gente precisa de transformação não-linear, que é o próximo capítulo."

**Pergunta provável:** "Por que mostrar StandardScaler se não resolve o problema?"
**Resposta:** porque é pré-requisito para PCA, clustering, regressão. E porque
ele *centra* as escalas, ainda que não comprima cauda. Engenharia de variáveis
costuma combinar lineares + não-lineares.
