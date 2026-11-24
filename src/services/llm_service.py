import hashlib, json, os, time
from google import genai
from google.genai import types
from openai import OpenAI
from PIL import Image
from src.config import GEMINI_API_KEY, GROQ_API_KEY, GROQ_MODEL, DEFAULT_MODEL, PROVEDOR
from src.schemas.diagnosis import DiagnosticReport

class MultimodalLLMService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
        self.groq_client = OpenAI(
            api_key=GROQ_API_KEY,
            base_url='https://api.groq.com/openai/v1'
        ) if GROQ_API_KEY else None
        self.cache = {}
        self.fallback_models = [
            DEFAULT_MODEL,
            'gemini-3.7-flash',
            'gemini-3.1-flash-lite',
            'gemini-3.5-flash-lite',
        ]

    def _normalize_actions(self, report_dict):
        actions = report_dict.get('acoes_recomendadas', [])
        if isinstance(actions, str):
            text = actions.strip()
            if text:
                parts = text.replace('•', '\n').split('\n')
                normalized = []
                for part in parts:
                    item = part.strip()
                    item = item.lstrip('0123456789.-) ')
                    if item:
                        normalized.append(item)
                report_dict['acoes_recomendadas'] = normalized
            else:
                report_dict['acoes_recomendadas'] = []
        return report_dict

    def _generate_groq(self, user_content):
        if not self.groq_client:
            return None
        try:
            groq_response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {'role': 'system', 'content': (
                        'Responda exclusivamente com JSON válido, seguindo exatamente estas '
                        'chaves: simbolo_identificado, gravidade_urgencia, '
                        'significado_manual, prognostico_contextual, acoes_recomendadas '
                        'e resumo_oficina. acoes_recomendadas deve ser uma lista JSON de strings.'
                    )},
                    {'role': 'user', 'content': user_content}
                ],
                response_format={'type': 'json_object'},
                temperature=0.2
            )
            report_dict = self._normalize_actions(
                json.loads(groq_response.choices[0].message.content)
            )
            return DiagnosticReport(**report_dict)
        except Exception as e:
            print(f'Fallback Groq com {GROQ_MODEL} falhou: {e}')
            return None

    def _generate_cache_key(self, prompt: str, image_path: str = None) -> str:
        content_str = prompt + (image_path if image_path else '')
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

    def manual_only_report(self, rag_context: str) -> DiagnosticReport:
        return self._manual_fallback(rag_context)

    def analyze_dashboard_alert(self, image_path: str, context_text: str, rag_context: str) -> DiagnosticReport:
        cache_key = self._generate_cache_key(context_text + rag_context, image_path)
        if cache_key in self.cache:
            print('Retornando resposta do cache local...')
            return self.cache[cache_key]

        prompt_system = (
            "Você é um especialista sênior em engenharia automotiva e diagnóstico veicular. "
            "Analise a imagem da luz de alerta do painel, a descrição enviada pelo motorista "
            "e o trecho relevante extraído do manual técnico do veículo via RAG. "
            "O conteúdo do RAG é uma fonte do manual oficial e deve ser tratado como a principal "
            "evidência textual disponível. Informe a página ou seção quando ela estiver identificada. "
            "Não diga que uma informação não foi localizada se ela estiver presente no contexto RAG. "
            "Gere um diagnóstico preciso em formato JSON estruturado."
        )

        user_content = (
            f"{prompt_system}\n\n"
            f"--- CONTEXTO DO MOTORISTA (Relato/Áudio) ---\n"
            f"{context_text}\n\n"
            f"--- CONTEXTO EXTRAÍDO DO MANUAL TÉCNICO (RAG) ---\n"
            f"{rag_context}\n\n"
            f"Por favor, identifique a luz no painel e forneça a análise completa de acordo com o esquema requerido."
        )

        contents = [user_content]
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            contents.append(img)

        if not self.client:
            return self._manual_fallback(rag_context)

        if PROVEDOR == 'groq':
            groq_report = self._generate_groq(user_content)
            if groq_report:
                groq_report_cache_key = cache_key
                self.cache[groq_report_cache_key] = groq_report
                return groq_report

        # Retentativa por modelo, reduzindo a dependência de uma única instância
        attempted_models = []
        for model_name in dict.fromkeys(self.fallback_models):
            attempted_models.append(model_name)
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type='application/json',
                            response_schema=DiagnosticReport,
                            temperature=0.2
                        )
                    )
                    report_dict = json.loads(response.text)
                    report = DiagnosticReport(**report_dict)
                    self.cache[cache_key] = report
                    return report
                except Exception as e:
                    print(f'Tentativa {attempt+1} com {model_name} falhou: {e}')
                    if attempt == 0:
                        time.sleep(2)

        if self.groq_client:
            try:
                groq_response = self.groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {'role': 'system', 'content': (
                            'Responda exclusivamente com JSON válido, seguindo exatamente estas '
                            'chaves: simbolo_identificado, gravidade_urgencia, '
                            'significado_manual, prognostico_contextual, acoes_recomendadas '
                            'e resumo_oficina.'
                        )},
                        {'role': 'user', 'content': user_content}
                    ],
                    response_format={'type': 'json_object'},
                    temperature=0.2
                )
                report_dict = json.loads(groq_response.choices[0].message.content)
                report = DiagnosticReport(**report_dict)
                self.cache[cache_key] = report
                return report
            except Exception as e:
                print(f'Fallback Groq com {GROQ_MODEL} falhou: {e}')

        # Fallback de segurança
        return DiagnosticReport(
            simbolo_identificado='Não foi possível confirmar pela IA',
            gravidade_urgencia='Médio',
            significado_manual=(
                'A IA está temporariamente indisponível. Consulte os trechos recuperados '
                'do manual na seção "Detalhes Técnicos & RAG".'
            ),
            prognostico_contextual='Erro temporário de conexão ou processamento na API de IA.',
            acoes_recomendadas=[
                'Tente novamente em alguns minutos',
                'Consulte os trechos oficiais recuperados pelo RAG',
                'Se houver risco imediato, procure assistência profissional'
            ],
            resumo_oficina=(
                'Diagnóstico por IA não concluído devido à indisponibilidade temporária '
                'dos modelos Gemini.'
            )
        )

    def _manual_fallback(self, rag_context: str) -> DiagnosticReport:
        extracted_context = rag_context.strip() if rag_context else ''
        return DiagnosticReport(
            simbolo_identificado='Consulta ao manual técnico',
            gravidade_urgencia='Não determinada',
            significado_manual=extracted_context or 'Nenhum trecho do manual foi encontrado.',
            prognostico_contextual='Resposta gerada pelo RAG sem processamento adicional de IA.',
            acoes_recomendadas=[
                'Leia o trecho recuperado do manual',
                'Confirme a versão e a página do seu veículo'
            ],
            resumo_oficina=extracted_context or 'Nenhum trecho técnico localizado.'
        )
