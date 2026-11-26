# Uso e estimativa de custos das APIs

## O que é registrado

Cada solicitação iniciada e tentativa de chamada externa gera uma linha em `logs/usage.csv`. O arquivo inclui identificador da solicitação, tipo de amostra (`observed` ou `synthetic`), modalidade, provedor, modelo, operação, sucesso ou falha, latência, tokens de entrada/saída quando informados pela API, duração de áudio quando disponível e custo estimado. Não são gravados prompts, transcrições, imagens, textos do usuário nem chaves de API. O arquivo fica local e é ignorado pelo Git.

Tentativas e retentativas são registradas separadamente. O evento `request_started` permite contar também solicitações sem chamada externa; o estimador as identifica como incompletas em vez de assumir custo zero. Uma resposta em cache local aparece como `cache_hit` e tem custo zero de API. Quando a tarifa ou os dados de uso não estão configurados/disponíveis, o custo fica vazio; não é contabilizado como zero.

## Tarifas de referência

Valores de lista consultados para o cálculo, sujeitos a alteração:

| Provedor/modelo | Entrada | Saída/áudio | Base de cálculo |
| --- | ---: | ---: | --- |
| Google Gemini 3.8 Flash, até 31/12/2026 | US$ 0,75 / 1 milhão de tokens | US$ 3,75 / 1 milhão de tokens | Tokens de entrada e saída informados pela API |
| Google Gemini 3.8 Flash, a partir de 01/01/2027 | US$ 1,50 / 1 milhão de tokens | US$ 7,50 / 1 milhão de tokens | Tokens de entrada e saída informados pela API |
| Google Gemini 3.1 Flash-Lite | US$ 0,25 / 1 milhão de tokens | US$ 1,50 / 1 milhão de tokens | Tokens de entrada e saída informados pela API |
| Groq `openai/gpt-oss-20b` | US$ 0,075 / 1 milhão de tokens | US$ 0,30 / 1 milhão de tokens | Tokens de entrada e saída informados pela API |
| Groq `whisper-large-v3-turbo` | — | US$ 0,04 / hora de áudio | Duração retornada pela transcrição |

Fontes: [preços da Gemini API](https://ai.google.dev/gemini-api/docs/pricing), [documentação Gemini 3.8 Flash](https://aistudio.google.com/docs/models/gemini-3.8-flash), [anúncio oficial Gemini 3.1 Flash-Lite e preço](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-lite/), [modelos e preços Groq](https://console.groq.com/docs/models) e [speech-to-text Groq](https://console.groq.com/docs/speech-to-text). Tarifas de modelos sem configuração explícita não são presumidas.

## Estimativa mensal

O cenário solicitado considera **50 usuários × 10 consultas por dia × 30 dias = 15.000 consultas/mês**. Após acumular registros representativos, execute na raiz do projeto:

```bash
python -m tests.estimate_monthly_cost
```

O estimador agrupa chamadas por `request_id`, soma as chamadas tarifadas de cada solicitação, calcula o custo médio por modalidade a partir das solicitações completas e pondera pelo mix de modalidades observado:

```text
custo mensal = 15.000 × Σ (participação observada da modalidade × custo médio por solicitação completa nessa modalidade)
```

É possível alterar o cenário com `--users`, `--queries-per-day` e `--days`, e indicar outro arquivo CSV com `--log`. Solicitações sintéticas são excluídas das médias. Se uma modalidade observada não tiver amostras completas, o custo total projetado será indicado como indisponível, em vez de apresentar um valor artificialmente baixo. A saída informa solicitações incompletas e alerta quando houver menos de cinco solicitações completas em alguma modalidade; nesse caso, o resultado é apenas preliminar e a amostra deve ser ampliada.

### Amostra local atual (26/11/2026)

Há **1 solicitação observada completa de texto** no CSV; uma chamada sintética de validação foi excluída. O custo observado nessa solicitação foi **US$ 0,000412** (2.667 tokens de entrada e 708 de saída, Groq `openai/gpt-oss-20b`). Se todas as 15.000 solicitações mensais fossem iguais a essa consulta textual, a projeção seria **US$ 6,19/mês**. Isto é apenas uma extrapolação ilustrativa de uma amostra única: ainda não há amostra de imagem/áudio nem distribuição representativa de modalidades, portanto não é uma estimativa mensal confiável do uso real.

Testes controlados com imagem/áudio sintéticos (excluídos das médias) registraram: uma resposta Gemini 3.1 Flash-Lite com 4.064 tokens de entrada e 341 de saída, estimada em **US$ 0,001528**; a mesma solicitação teve quatro tentativas anteriores Gemini sem metadados de uso, portanto seu custo total não é conhecido. A transcrição Whisper de 12,99 s custou **US$ 0,000144** e a chamada Groq subsequente teve custo estimado de **US$ 0,000413**. Em teste ponta a ponta posterior, a equipe confirmou que o áudio foi processado e a interface exibiu o diagnóstico. Os custos medidos referem-se às chamadas sintéticas registradas e permanecem excluídos da projeção mensal.

## Limitações

- Antes de haver chamadas reais, não há médias empíricas suficientes para um valor mensal confiável. O comando deve ser executado depois de acumular uso representativo de cada modalidade.
- Chamadas com falha ou sem tarifa/uso conhecido são incompletas e ficam fora da média de custo daquela modalidade; a projeção informa essa quantidade.
- A participação de cada modalidade reflete apenas o mix observado na amostra local e pode não representar usuários futuros.
- Os valores são estimativas de preço de lista, não uma fatura. Créditos, cotas gratuitas, descontos, região e alterações de preço podem mudar o gasto efetivo.
- O log é local, pode ser apagado e não é sincronizado nem enviado ao repositório. Faça uma cópia segura se precisar preservar a amostra para o relatório final.
