import gradio as gr
from src.services.stt_service import STTService
from src.services.rag_service import RAGService
from src.services.llm_service import MultimodalLLMService

stt_service = STTService()
rag_service = RAGService(manuals_dir='manuals')
llm_service = MultimodalLLMService()

def process_diagnostic(image, audio, user_text):
    # 1. Processa áudio se enviado
    transcribed_text = ''
    if audio:
        transcribed_text = stt_service.transcribe_audio(audio)
    
    full_context = (
        f"Relato por escrito: {user_text or 'Nenhum'}\n"
        f"Transcrição do áudio: {transcribed_text or 'Nenhuma'}"
    )
    
    # 2. RAG no manual do veículo
    search_query = f"{user_text} {transcribed_text}".strip()
    if not search_query:
        search_query = "diagnóstico luz de alerta painel automotivo"
    rag_context = rag_service.search_manual(query=search_query, top_k=3)
    
    # 3. Análise Multimodal LLM
    if not image and not audio:
        report = llm_service.manual_only_report(rag_context)
    else:
        report = llm_service.analyze_dashboard_alert(
            image_path=image,
            context_text=full_context,
            rag_context=rag_context
        )
    
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

def prepare_diagnostic(user_text):
    return (
        user_text,
        gr.update(value='⏳ Analisando...', interactive=False),
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
        
        with gr.Column():
            output_report = gr.Markdown(label='Diagnóstico')
            with gr.Accordion('🔍 Detalhes Técnicos & RAG', open=False):
                transcription_out = gr.Textbox(label='Transcrição de Áudio (STT)')
                rag_out = gr.Textbox(label='Trechos do Manual Recuperados (RAG Multimodal)', lines=6)
                
    btn_submit.click(
        fn=prepare_diagnostic,
        inputs=[text_input],
        outputs=[captured_text, btn_submit, text_input],
        queue=False
    ).then(
        fn=process_diagnostic,
        inputs=[img_input, audio_input, captured_text],
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
