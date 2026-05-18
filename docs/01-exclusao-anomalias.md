# 01 — Exclusão de anomalias

## Slide 1: O que é
- Remover **registros que comprometem a análise**: nulos, duplicatas, valores impossíveis, outliers de origem suspeita.
- Distinguir **outlier real** (precisa investigar) de **outlier informativo** (manter — é o objeto de estudo).
- Sempre justificar a remoção: *por que* aquele registro não pertence.

## Slide 2: Cuidados
- **Nulos:** drop só de colunas onde o nulo é indecifrável. Em colunas opcionais (ex: `caption_text`), imputar string vazia é melhor.
- **Outliers:** IQR é um sinalizador, não um veredito. No nosso caso, os "outliers" de likes são justamente os virais — manter.
- **Duplicatas:** identificar a chave única real (`media_pk`, `comment_pk`), não confiar em todas as colunas.
- **Perfis suspeitos:** ratio engagement/followers extremamente alto pode ser bot ou conta nova.

## Slide 3: O que fizemos no projeto
- Filtramos 3 perfis problemáticos coletados: 1 privado (`gordonramsayofficial` com 87 followers), 1 inexistente (`codeshow.br`), 1 conta nova (`dev.eficiente` com 1 follower).
- Removemos posts sem `taken_at` ou `like_count` (essenciais para qualquer análise temporal/engajamento).
- Mantivemos posts com likes acima do IQR — eles são os "virais" que queremos estudar.
- **Resultado:** de ~19 perfis brutos para 16 perfis válidos, ~385 posts limpos.

## Notas do apresentador
> "Olha esse caso: a Hiker retornou o perfil 'gordonramsayofficial' com 87 seguidores.
> O Gordon Ramsay real tem 17 milhões. Existem várias contas com nomes parecidos —
> e a engenharia de variáveis começa exatamente aqui: percebendo que esse dado não
> faz sentido e tirando fora antes de comparar com o Cristiano. Se você não tira,
> seu gráfico de engajamento médio vai mentir."

**Pergunta provável da turma:** "Por que não removeram os outliers de likes?"
**Resposta:** porque a pergunta do projeto é "o que torna um post viral?" — outlier
é exatamente o sinal, não o ruído. A escala log resolve o problema visual.
