import gradio as gr
from pathlib import Path
from uuid import uuid4
from src.services.stt_service import STTService
from src.services.rag_service import RAGService
from src.services.llm_service import LLMProviderError, MultimodalLLMService
from src.services.usage_service import record_request_start

stt_service = STTService()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
rag_service = RAGService(manuals_dir=str(PROJECT_ROOT / 'manuals'))
llm_service = MultimodalLLMService()

def process_diagnostic(image, audio, user_text, request_id, modality):
    record_request_start(request_id, modality)
    # 1. Processa áudio se enviado
    transcribed_text = ''
    if audio:
        transcribed_text = stt_service.transcribe_audio(audio, request_id, modality)
    
    full_context = (
        f"Relato por escrito: {user_text or 'Nenhum'}\n"
        f"Transcrição do áudio: {transcribed_text or 'Nenhuma'}"
    )
    
    # 2. RAG no manual do veículo
    search_query = f"{user_text} {transcribed_text}".strip()
    if not search_query:
        search_query = "diagnóstico luz de alerta painel automotivo"
    rag_context = rag_service.search_manual(query=search_query, top_k=3)
    
    # 3. Envia imagens ao Gemini; consultas sem imagem usam o provedor configurado.
    try:
        report = llm_service.analyze_dashboard_alert(
            image_path=image,
            context_text=full_context,
            rag_context=rag_context,
            request_id=request_id,
            modality=modality,
        )
    except LLMProviderError as error:
        output_md = f"""### ⚠️ Não foi possível concluir a análise

{error}
"""
        return output_md, transcribed_text, rag_context
    
    # Formata saída para a interface
    actions = '\n'.join([f'- {act}' for act in report.acoes_recomendadas])
    output_md = f"""### 🚗 Diagnóstico Inteligente Veicular

**Símbolo Identificado:** {report.simbolo_identificado}  
**Nível de Urgência:** {report.gravidade_urgencia}

#### 📖 Significado (Manual Oficial):
{report.significado_manual}

#### 🛠️ Prognóstico Contextual:
{report.prognostico_contextual}

#### ✅ Ações Recomendadas:
{actions}

---
#### 📋 Resumo para Mecânico/Oficina:
> *{report.resumo_oficina}*
"""
    
    return output_md, transcribed_text, rag_context

def get_modality(image, audio):
    if image and audio:
        return 'image+audio'
    if image:
        return 'image'
    if audio:
        return 'audio'
    return 'text'


def prepare_diagnostic(user_text, image, audio):
    return (
        user_text,
        str(uuid4()),
        get_modality(image, audio),
        gr.update(value='⏳ Analisando...', interactive=False),
        gr.update(value=''),
        gr.update(value=''),
        gr.update(value='')
    )

def reset_diagnostic_button():
    return gr.update(value='🔍 Enviar', interactive=True)

def reset_diagnostic():
    return (
        gr.update(value=None),
        gr.update(value=None),
        gr.update(value=''),
        gr.update(value=''),
        gr.update(value=''),
        gr.update(value=None),
        gr.update(value='🔍 Enviar', interactive=True)
    )

with gr.Blocks(title='GuiaDeBordo IA Automotivo') as demo:
    gr.Markdown('# 🚘 GuiaDeBordo IA Automotivo')
    gr.Markdown('Faça o upload da foto do painel e descreva as circunstâncias por áudio ou texto.')
    
    with gr.Row():
        with gr.Column():
            img_input = gr.Image(type='filepath', label='📷 Foto do Painel / Alerta')
            audio_input = gr.Audio(sources=['microphone', 'upload'], type='filepath', label='🎙️ Gravação das Circunstâncias (Áudio)')
            text_input = gr.Textbox(lines=3, placeholder='Descreva a velocidade, barulho, clima ou comportamento do carro...', label='📝 Detalhes em Texto')
            btn_submit = gr.Button('🔍 Enviar', variant='primary')
            btn_new = gr.Button('🔄 Nova análise', variant='primary')
            captured_text = gr.State()
            request_id_state = gr.State()
            modality_state = gr.State()
        
        with gr.Column():
            output_report = gr.Markdown(label='Diagnóstico')
            with gr.Accordion('🔍 Detalhes Técnicos & RAG', open=False):
                transcription_out = gr.Textbox(label='Transcrição de Áudio (STT)')
                rag_out = gr.Textbox(label='Trechos do Manual Recuperados (RAG Multimodal)', lines=6)
                
    btn_submit.click(
        fn=prepare_diagnostic,
        inputs=[text_input, img_input, audio_input],
        outputs=[
            captured_text,
            request_id_state,
            modality_state,
            btn_submit,
            output_report,
            transcription_out,
            rag_out
        ],
        queue=False
    ).then(
        fn=process_diagnostic,
        inputs=[img_input, audio_input, captured_text, request_id_state, modality_state],
        outputs=[output_report, transcription_out, rag_out]
    ).then(
        fn=reset_diagnostic_button,
        outputs=[btn_submit]
    )

    btn_new.click(
        fn=reset_diagnostic,
        outputs=[
            img_input,
            audio_input,
            text_input,
            output_report,
            transcription_out,
            rag_out,
            btn_submit
        ]
    )

if __name__ == '__main__':
    demo.launch(server_name='127.0.0.1', server_port=7860, share=True)
