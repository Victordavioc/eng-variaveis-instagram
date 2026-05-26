# 07: LLM como engenheiro de variáveis

## Slide 1: O que é
- Usar um **Large Language Model** (Gemini, GPT-4, Claude) como extrator de **features semânticas** sobre texto não-estruturado.
- Substitui (ou complementa) regex, dicionários de palavras e modelos clássicos de NLP.
- É **o estado-da-arte para features sobre texto** desde 2023.

## Slide 2: Quando usar / cuidados
- Use para tarefas onde **regex falha** ou **dicionários são frágeis**:
  - Classificação temática de captions (gírias, emojis, mistura de idiomas).
  - Sentimento (ironia, contexto, sarcasmo).
  - Extração de entidades (marcas, locais, eventos).
- **Custo e latência:** cada chamada tem latência (~500ms-2s) e custo. **Batches são obrigatórios.**
- **Cache em disco:** chave = `sha256(model + prompt)`. Re-executar não chama o LLM.
- **Forçar JSON estruturado:** parâmetro `response_mime_type="application/json"` (Gemini) ou Tool Use (Claude). Evita parsing frágil.
- **Validação:** sempre prever fallback (`"outro"`, `"neutro"`) caso o LLM retorne lixo.

## Slide 3: O que fizemos no projeto
- **3 tipos de features** extraídas com Gemini 2.5 Flash:
  1. `theme`: classificação temática das captions em 8 categorias (LLM → ~14 batches em cache).
  2. `entities`: lista de marcas/pessoas/locais por caption (LLM + fallback regex 50/50).
  3. `sentiment`: classificação positivo/neutro/negativo dos comentários (LLM + fallback lexicon).
- **Batches de 25 inputs por prompt**: reduz nº de chamadas em ~25× (e o custo).
- **Cache em `data/processed/llm_cache.json`**: re-rodar o notebook custa **0 chamadas**.
- **Pipeline híbrido com degradação graciosa:** cada feature derivada do LLM tem uma
  coluna `*_source` ∈ {`llm`, `fallback`, `empty`} indicando como foi obtida. Se o LLM
  fica fora do ar (rate-limit, quota), o fallback determinístico assume e o pipeline
  continua funcionando.
- **Resultado:** transformamos texto livre em colunas estruturadas que **alimentam** as seções de cruzamento e análise final, **sem nunca quebrar** por causa de uma dependência externa.

## Notas do apresentador
> "Antes, se eu quisesse classificar uma caption como 'esporte' ou 'lifestyle',
> teria que manter um dicionário de palavras-chave, lidar com português + inglês,
> com emojis, com gírias. Era frágil. Hoje, um prompt de 5 linhas faz isso,
> e funciona melhor. Mas atenção: continua sendo engenharia de variáveis. A
> diferença é a ferramenta."

**Pergunta provável:** "Isso não é caro?"
**Resposta:** com batches e cache, ~60 chamadas totais cobriram todo o dataset.
No tier gratuito do Gemini, custou zero. Em produção, é custo previsível e
amortizado pelo cache.
