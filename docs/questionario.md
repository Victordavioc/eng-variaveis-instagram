# Questionário — Engenharia de Variáveis com Dados do Instagram

> **Instruções:** 10 questões de múltipla escolha. Você terá 15 minutos.
> Marque apenas uma alternativa por questão. Boa prova!

---

## Pergunta 1 (Exclusão de anomalias)

Durante a coleta de dados de perfis do Instagram, encontramos uma conta com nome
parecido com a oficial do Gordon Ramsay, mas com apenas 87 seguidores e 197 posts.
Qual a abordagem mais correta?

a) Manter o perfil — todos os dados coletados devem ser preservados para evitar viés.
b) Remover o perfil — provavelmente é uma conta secundária ou homônima que distorceria comparações entre tiers.
c) Combinar com a conta oficial somando os seguidores.
d) Imputar o valor de seguidores pela média dos macro influenciadores.

**Resposta correta:** b)
**Explicação:** dados claramente fora do esperado para um perfil oficial devem ser removidos com justificativa documentada. Manter geraria um falso "outlier" que confundiria a análise.

---

## Pergunta 2 (Exclusão de anomalias)

Em uma análise de posts do Instagram, encontramos 5 posts com `like_count` muito acima do IQR superior (Cristiano Ronaldo). Qual a melhor decisão?

a) Remover, pois são outliers que distorcem a média.
b) Substituir o valor pelo terceiro quartil (winsorização agressiva).
c) Manter, mas aplicar `log1p` em análises e visualizações.
d) Excluir o perfil inteiro, pois um perfil tão influente não pode ser comparado.

**Resposta correta:** c)
**Explicação:** outliers de engajamento são exatamente o objeto de estudo — são os posts virais. O problema é de *escala*, não de *integridade*. Manter e aplicar transformação log resolve a visualização sem perder informação.

---

## Pergunta 3 (Discretização)

Usamos `pd.cut(follower_count, bins=[0, 100_000, 1_000_000, inf], labels=["micro","mid","macro"])`. Por que `pd.cut` e não `pd.qcut`?

a) `pd.qcut` não aceita labels customizados.
b) Os bins foram definidos por **convenção do domínio** (categoria de mercado), não pela distribuição dos dados.
c) `pd.cut` é mais rápido em DataFrames grandes.
d) `pd.qcut` exige normalidade dos dados.

**Resposta correta:** b)
**Explicação:** `pd.cut` usa bins explícitos, ideal quando há critério de domínio (micro/mid/macro é convenção de mercado). `pd.qcut` divide por quantis dos dados — usaríamos se quiséssemos 4 grupos balanceados.

---

## Pergunta 4 (Discretização)

Aplicamos `pd.qcut(like_count, q=4, labels=["baixo","médio","alto","viral"])`. O que isso garante?

a) Cada faixa contém aproximadamente o mesmo **número de posts**.
b) Cada faixa cobre o mesmo **intervalo de likes**.
c) Cada faixa tem a mesma **média de engajamento**.
d) Posts virais terão `engagement_rate` acima de 5%.

**Resposta correta:** a)
**Explicação:** `qcut` divide por quantis — o resultado tem ~25% dos registros em cada faixa. Os intervalos de likes serão muito diferentes entre as faixas porque a distribuição é desbalanceada.

---

## Pergunta 5 (Decomposição)

Decompusemos `taken_at` em ano, mês, hora, período do dia, etc. Qual é a principal vantagem?

a) Reduz o uso de memória do DataFrame.
b) Cria múltiplas features novas a partir de uma só, permitindo perguntas como "qual horário rende mais?".
c) Garante que o campo original possa ser removido com segurança.
d) Converte automaticamente para o fuso horário do usuário.

**Resposta correta:** b)
**Explicação:** decomposição é aditiva (não substitui o campo original) e cria várias dimensões independentes que podem ser correlacionadas, agrupadas e cruzadas. Não tem a ver com memória nem com fuso.

---

## Pergunta 6 (Cruzamento)

Criamos `engagement_rate = (likes + comments) / followers`. Por que isso é melhor que usar `likes` direto para comparar perfis?

a) Não é melhor — `likes` é a métrica oficial do Instagram.
b) Porque `engagement_rate` é uma **feature normalizada** que permite comparar perfis com bases de seguidores muito diferentes.
c) Porque `comments` tem peso maior que `likes`.
d) Porque elimina automaticamente posts virais.

**Resposta correta:** b)
**Explicação:** likes absolutos favorecem perfis grandes. Dividir pela base normaliza, permitindo comparar Cristiano (600M) com um micro (10k) na mesma escala. É um cruzamento clássico (operação entre colunas).

---

## Pergunta 7 (Transformações lineares)

`StandardScaler` aplicada em `like_count` produz uma distribuição com média 0 e desvio 1. Qual afirmação é verdadeira?

a) A distribuição agora é normal.
b) A *forma* da distribuição muda, mas a cauda longa desaparece.
c) Os valores foram centralizados/escalados, mas a *forma* (e a cauda longa) permanece a mesma.
d) Os outliers foram removidos.

**Resposta correta:** c)
**Explicação:** padronização é transformação linear (`(x - μ)/σ`). Centraliza e escala, mas não muda a forma da distribuição. Para domar cauda longa, precisa de transformação não-linear (log, Yeo-Johnson).

---

## Pergunta 8 (Transformações não-lineares)

Por que usamos `np.log1p(like_count)` em vez de `np.log(like_count)`?

a) Por compatibilidade com versões antigas do NumPy.
b) `log1p` é mais rápido.
c) `log(0)` é indefinido (−∞); `log1p(0) = 0` evita perder posts sem likes.
d) `log1p` preserva o sinal de valores negativos.

**Resposta correta:** c)
**Explicação:** `log1p(x) = log(1 + x)` permite lidar com `x = 0` sem produzir −∞. Posts podem ter 0 comentários, e perder essas linhas distorceria a análise.

---

## Pergunta 9 (Transformações não-lineares)

Usamos `PowerTransformer(method="yeo-johnson")` em `engagement_rate`. Por que Yeo-Johnson e não Box-Cox?

a) Box-Cox é mais lento.
b) Box-Cox exige `x > 0`. Yeo-Johnson aceita zeros e negativos — necessário porque `engagement_rate` pode ser 0.
c) Yeo-Johnson é determinística e Box-Cox é estocástica.
d) Box-Cox foi descontinuada no scikit-learn.

**Resposta correta:** b)
**Explicação:** Box-Cox é uma generalização do log e exige `x > 0`. Yeo-Johnson estende para aceitar zeros e negativos, sendo a escolha mais robusta na prática.

---

## Pergunta 10 (LLM como engenharia de variáveis)

Usamos Gemini para classificar `theme` das captions e `sentiment` dos comentários. Por que isso é considerado **engenharia de variáveis**?

a) Não é — o LLM é uma ferramenta de NLP, não de feature engineering.
b) Porque transformamos **texto não-estruturado** em **colunas categóricas estruturadas** que alimentam análises subsequentes — exatamente o objetivo da engenharia de variáveis.
c) Porque o Gemini foi treinado especificamente para feature engineering.
d) Porque o LLM substitui completamente todas as outras técnicas.

**Resposta correta:** b)
**Explicação:** engenharia de variáveis é o ato de transformar dados brutos em features úteis. Antes era feita com regex e dicionários; hoje LLMs fazem o mesmo papel sobre texto, com resultados melhores. A ferramenta mudou; o conceito permanece.

---

## Gabarito rápido

| # | resp |
|---|---|
| 1 | b |
| 2 | c |
| 3 | b |
| 4 | a |
| 5 | b |
| 6 | b |
| 7 | c |
| 8 | c |
| 9 | b |
| 10 | b |
