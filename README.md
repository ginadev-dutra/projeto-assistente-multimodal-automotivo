# 🚘 Assistente Multimodal de Diagnóstico Automotivo com RAG - GuiaDeBordo IA Automotivo

Aplicação desenvolvida para o Trabalho Orientado da pós-graduação em **Desenvolvimento de Aplicações Interativas com LLMs Multimodais** (PUC Minas).

## 📌 Visão Geral da Solução
A aplicação combina Inteligência Artificial Multimodal (Visão + Áudio + Texto) e **RAG (Retrieval-Augmented Generation)** para interpretar avisos de painel automotivo a partir de fotos, analisar relatos em áudio do motorista (condições da pista, velocidade, ruídos) e consultar automaticamente o manual técnico do veículo.

### 🎯 Principais Funcionalidades
1. **Identificação Visual do Alerta:** Processamento de imagem do painel via LLM multimodal.
2. **Transcrição e Análise de Contexto:** Transcrição de áudio via Whisper (Groq) combinando relato contextual do usuário.
3. **RAG no Manual Técnico:** Ingestão de manuais em PDF, vetorização e busca semântica em banco vetorial (ChromaDB).
4. **Diagnóstico Estruturado:** Geração de JSON validado via Pydantic contendo gravidade, significado, prognóstico, ações imediatas e síntese para concessionária/oficina.
5. **Interface Web Interativa:** Desenvolvida em Gradio com suporte a upload de imagem, gravação de áudio e streaming de resultados.

---

## 🏗️ Estrutura do Projeto

```text
.
├── app/
│   └── app.py                  # Interface Gradio e orquestração do fluxo
├── src/
│   ├── config.py               # Configuração e variáveis de ambiente
│   ├── schemas/                # Modelos Pydantic
│   └── services/               # LLM, transcrição e RAG
├── prompts/                    # Prompts versionados
├── dados/
│   └── exemplos/
│       ├── perguntas_rag.json  # Casos de avaliação com respostas esperadas
│       ├── painel_sintetico.png
│       └── relato_sintetico.wav
├── manuals/                    # Manual PDF usado pelo RAG
├── tests/                      # Avaliação RAG, custos e fluxos de erro
├── docs/                       # Arquitetura, dados e documentação de custos
│   ├── architecture_and_data.md
│   ├── api_costs.md
│   ├── generate_report.py
│   ├── relatorio_desenvolvimento.pdf
│   ├── evidencias_caso_sintetico.png
│   └── evidencias_erro_gemini.png
├── .env.example                # Nomes das variáveis, sem segredos
├── REGISTRO_IA.md              # Registro transparente do uso de IA
├── requirements-report.txt     # Dependência opcional para gerar o PDF
└── requirements.txt
```

---

## ⚡ Como Rodar o Projeto no VS Code

### 1. Preparar o Ambiente Virtual (`venv`)
No terminal integrado do VSCode:
```bash
# Para criar o ambiente:
python -m venv .venv

# Para ativar no Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Para desativar:
deactivate
# No Linux/macOS, ative com:
source .venv/bin/activate
```

### 2. Instalar as Dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar as Variáveis de Ambiente
Copie `.env.example` para `.env` e preencha as chaves necessárias:

```env
GEMINI_API_KEY=sua_chave_gemini
GROQ_API_KEY=sua_chave_groq
PROVEDOR=groq
GEMINI_MODEL=gemini-3.8-flash
GROQ_MODEL=openai/gpt-oss-20b
```

O arquivo `.env` já está incluído no `.gitignore` e não deve ser enviado ao repositório.
Análises com imagem usam o Gemini, que recebe a foto. Consultas sem imagem usam o provedor definido em `PROVEDOR` e podem recorrer ao outro provedor se necessário.

### 4. Adicionar o Manual Técnico em PDF
Coloque o manual do veículo em PDF na pasta `manuals/`.

### 5. Executar a Aplicação
Na raiz do repositório, execute:

```bash
python -m app.app
```

Acesse a aplicação no navegador com o link que será fornecido no terminal. 

### Executar a avaliação de recuperação RAG
Com o ambiente virtual ativado, na raiz do projeto, compare a busca semântica atual, a expansão simples de consulta, BM25 e janelas de páginas:

```bash
python -m tests.evaluate_rag
```

### Uso e estimativa de custos das APIs
As chamadas a Gemini, Groq e Whisper registram localmente tokens (quando informados), latência, modalidade e custo estimado em `logs/usage.csv`. O log não contém prompts nem conteúdo enviado pelo usuário e não é versionado.

Para estimar o cenário mensal de 50 usuários × 10 consultas/dia × 30 dias com base na mistura observada:

```bash
python -m tests.estimate_monthly_cost
```

Tarifas, fórmula, limitações e opções para alterar o cenário estão em [docs/api_costs.md](docs/api_costs.md). A estimativa exige registros representativos; valores desconhecidos não são tratados como custo zero.
Depois de gerar registros com análises representativas, rode o estimador; a aplicação não precisa permanecer aberta.

### Gerar o relatório PDF
O PDF entregue está em `docs/relatorio_desenvolvimento.pdf`. Para regenerá-lo no Windows, instale a dependência opcional e execute na raiz do projeto:

```powershell
pip install -r requirements-report.txt
python docs\generate_report.py
```

O gerador monta o relatório com as evidências locais em `docs/`; mantenha as imagens de evidência nesse diretório.

### Arquitetura, dados e contexto
O fluxo do app, a origem e a quantidade dos dados, os cuidados de privacidade/direitos de uso e a justificativa do RAG estão em [docs/architecture_and_data.md](docs/architecture_and_data.md). O manual utilizado é uma publicação oficial da Volkswagen; consulte as observações de direitos antes de redistribuí-lo.

O [relatório de desenvolvimento em PDF](docs/relatorio_desenvolvimento.pdf) e as [evidências da interface](docs/) foram preparados com testes controlados. As entradas de demonstração são sintéticas e estão identificadas como tal.

---

## 🏛️ Infraestrutura e Resiliência
- **Resiliência e Fallback:** Implementação de retentativas exponenciais em caso de oscilações de API.
- **Gestão de Custos:** Sistema de cache de requisições baseado no hash SHA-256 das entradas para evitar chamadas redundantes a APIs pagas.
- **Saídas Garantidas:** Utilização do Pydantic para garantir que o formato do relatório obedeça estritamente ao contrato de dados estabelecido.
