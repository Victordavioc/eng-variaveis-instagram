# 08: Conclusão analítica

## O que descobrimos

> *Esse é o slide de encerramento. Os números absolutos saem do notebook,
> use os valores que aparecerem no `summary` da Seção 9 na hora de apresentar.*

### Insight 1: Saúde do perfil
- O scatter `engagement_rate × follower_count` (eixo X em log) revela que perfis
  **micro têm engagement_rate proporcionalmente maior** que macro.
- Perfis com seguidores ~0 e likes >0 foram detectados na Seção 2 e **filtrados**,
  são candidatos a bots ou contas vazias.
- **Conclusão:** "tamanho não é qualidade". Uma das descobertas mais importantes
  do dataset.

### Insight 2: Caption analysis
- O boxplot de likes por `theme` mostra que captions classificadas como
  `esporte` e `lifestyle` tendem a concentrar mais likes (efeito do tier:
  Cristiano, Messi, Kylie publicam nesses temas).
- A correlação entre `caption_length` e `likes` é fraca, **caption longa não
  garante engajamento**.
- As entidades extraídas pelo LLM mostram que marcas (Nike, Adidas) e times
  (Real Madrid, Inter Miami) aparecem nas captions de maior engajamento.

### Insight 3: Comportamento da audiência
- A distribuição de `sentiment` dos comentários é **majoritariamente positiva**
  em todos os tiers, fãs comentam mais que críticos.
- Comentários **negativos concentram em posts polêmicos** (alto `comments_per_like`).
- Micro influenciadores recebem comentários ligeiramente mais neutros, audiência
  menor, mais técnica.

### Insight 4: Comparação entre tiers
| Métrica | Micro | Mid | Macro |
|---|---|---|---|
| Likes médios | dezenas | centenas | dezenas/centenas de milhares |
| Engagement rate | **maior** | médio | menor |
| Caption típica | educacional | promocional | lifestyle/esporte |
| Sentimento dos comentários | mais neutro | balanceado | mais positivo |

## Por que a engenharia de variáveis foi essencial

Nenhum desses 4 insights existe **diretamente nos dados brutos**. Cada um foi
*construído*:

- "engagement_rate": não existia, foi cruzado a partir de likes/followers (Seção 6).
- "tier": não existia, foi discretizado de follower_count (Seção 5).
- "theme" e "sentiment": não existiam, foram extraídos por LLM (Seção 4).
- A visualização honesta só é possível com log nos eixos (Seção 8).

> **Mensagem final:** *engenharia de variáveis não é pré-processamento, é
> a construção do significado que está latente nos dados.*

## Notas do apresentador
- Reservar 5-7 minutos para esse slide.
- Mostrar a tabela `summary` ao vivo no notebook (Seção 9, última célula).
- Encerrar com: *"todas as conclusões dependeram de features que tivemos que
  construir do zero. Os dados crus só nos davam a matéria-prima."*
