# Linha de base da recuperação RAG

- Data: 26/11/2026
- Corpus: manual PDF em `manuals/` (270 páginas extraídas)
- Estratégia avaliada: implementação atual, uma página por documento no ChromaDB
- Métrica: acerto@3; conta como acerto quando uma página esperada aparece entre as três primeiras
- Resultado: **8/10 (80%)**

| Caso | Páginas recuperadas (top 3) | Página esperada | Resultado |
| --- | --- | --- | --- |
| rag-01 | 139, 127, 9 | 139 | Acerto |
| rag-02 | 139, 122, 125 | 139 | Acerto |
| rag-03 | 209, 215, 216 | 209 | Acerto |
| rag-04 | 64, 39, 44 | 44 | Acerto |
| rag-05 | 128, 109, 8 | 128 | Acerto |
| rag-06 | 164, 167, 90 | 164 | Acerto |
| rag-07 | 170, 234, 232 | 170 | Acerto |
| rag-08 | 184, 115, 202 | 184 | Acerto |
| rag-09 | 196, 112, 36 | 195 | Erro |
| rag-10 | 198, 191, 98 | 197 | Erro |

Os dois erros recuperaram uma página próxima, mas não a página de referência definida no conjunto: a pergunta sobre o nível do óleo esperava a página 195 e retornou a 196; a pergunta sobre congelamento do líquido de arrefecimento esperava a página 197 e retornou a 198. Como o critério é recuperação da evidência esperada, ambos permanecem erros nesta linha de base.

Para repetir a medição na raiz do projeto:

```powershell
python -m tests.evaluate_rag
```

Esta medição avalia apenas recuperação de páginas; não mede se a resposta final do LLM está correta.

## Experimento: palavras-chave + Reciprocal Rank Fusion

- Consulta original e consulta compactada (remoção de palavras funcionais) são executadas separadamente.
- Cada consulta retorna até 10 páginas candidatas.
- Os rankings são combinados por Reciprocal Rank Fusion com constante 60.
- A estratégia é apenas experimental no avaliador; a busca usada pela aplicação não foi alterada.
- Resultado nos mesmos 10 casos: **9/10 (90%)**, contra 8/10 (80%) do baseline.

O caso rag-10 passou: a página 197 subiu para a 3ª posição. O caso rag-09 continua falhando: a página 195 não aparece no top 3 combinado. A melhora de 10 pontos percentuais é observada neste conjunto pequeno e não demonstra, por si só, que a estratégia generalizará para outras perguntas ou manuais.

O comando `python -m tests.evaluate_rag` agora imprime lado a lado o baseline e o experimento. Antes de adotar a fusão na aplicação, é necessário investigar o caso do óleo e testar em mais perguntas/manuais. A busca de produção continua inalterada.

## Experimento: busca lexical BM25 + RRF

Foi adicionada ao avaliador uma busca lexical BM25 sobre as páginas extraídas do manual, normalizando acentos. O ranking BM25 é combinado com o ranking semântico original por RRF. Nenhum pacote adicional e nenhuma chamada a API são necessários.

| Estratégia | Acerto@3 |
| --- | ---: |
| Busca semântica atual (baseline) | 8/10 (80%) |
| Consulta com palavras funcionais removidas + RRF | 9/10 (90%) |
| BM25 lexical + busca semântica + RRF | 9/10 (90%) |

O caso rag-10 continua acertando. O caso rag-09 permanece como erro: no BM25 isolado, a página correta 195 aparece em 5º lugar, atrás das páginas 225, 141, 196 e 194; a fusão atual não a eleva ao top 3. Portanto, BM25 não melhorou a métrica em relação à expansão simples de consulta. O resultado não justifica adotar a estratégia no app; a busca de produção segue inalterada.

## Experimento: janelas de páginas adjacentes

Também foram avaliados documentos sobrepostos formados pela concatenação de 2 ou 3 páginas consecutivas. O resultado é considerado acerto quando uma página esperada está contida em uma das janelas recuperadas no top 3.

| Estratégia | Acerto@3 |
| --- | ---: |
| Janelas sobrepostas de 2 páginas | 8/10 (80%) |
| Janelas sobrepostas de 3 páginas | 8/10 (80%) |

Nenhuma das duas configurações superou o baseline semântico de 8/10. Para rag-09, ambas priorizaram uma janela iniciada na página 196, sem incluir a página de referência 195. Janelas maiores também não melhoraram o resultado geral. Não foram adotadas na aplicação; o índice em produção permanece uma página por documento.
