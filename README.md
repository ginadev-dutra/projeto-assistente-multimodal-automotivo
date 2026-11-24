# 🚘 Assistente Multimodal de Diagnóstico Automotivo com RAG

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


---

## ⚡ Como Rodar o Projeto no VS Code

### 1. Preparar o Ambiente Virtual (`venv`)
No terminal integrado do VSCode:
```bash
# Para criar o ambiete: 
python -m venv .venv

# Para ativar o ambiente: 
.venv\Scripts\Activate.ps1

# Para desativar o ambiente: 
deactivate

# No Linux/macOS:
source .venv/bin/activate

# No Windows (PowerShell):
.venv\Scripts\Activate.ps1


### 3. Instalar as Dependências
pip install -r requirements.txt

### 4. Configurar as Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto com o seguinte exemplo:

```env
GEMINI_API_KEY=sua_chave_gemini
GROQ_API_KEY=sua_chave_groq
MODEL_NAME=gemini-3.8-flash
GROQ_MODEL=openai/gpt-oss-20b
```

O arquivo `.env` já está incluído no `.gitignore` e não deve ser enviado ao repositório.

### 5. Adicionar o Manual Técnico em PDF
Coloque o manual do carro (arquivo em PDF ) na pasta "manuals".

### 6. Executar a Aplicação
No terminal: python -m src.app

Acesse a aplicação no navegador com o link que será fornecido no terminal. 

---

## 🏛️ Infraestrutura e Resiliência
- **Resiliência e Fallback:** Implementação de retentativas exponenciais em caso de oscilações de API.
- **Gestão de Custos:** Sistema de cache de requisições baseado no hash SHA-256 das entradas para evitar chamadas redundantes a APIs pagas.
- **Saídas Garantidas:** Utilização do Pydantic para garantir que o formato do relatório obedeça estritamente ao contrato de dados estabelecido.
