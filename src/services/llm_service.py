import hashlib, json, os, time
from pathlib import Path
from google import genai
from google.genai import types
from openai import OpenAI
from PIL import Image
from src.config import GEMINI_API_KEY, GROQ_API_KEY, GROQ_MODEL, DEFAULT_MODEL, PROVEDOR
from src.schemas.diagnosis import DiagnosticReport
from src.services.usage_service import record_api_call

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIAGNOSIS_PROMPT = (PROJECT_ROOT / 'prompts' / 'diagnostico_v1.txt').read_text(encoding='utf-8')
GROQ_JSON_PROMPT = (PROJECT_ROOT / 'prompts' / 'groq_json_v1.txt').read_text(encoding='utf-8')


class LLMProviderError(RuntimeError):
    pass


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

    def _generate_groq(self, user_content, request_id, modality, sample_type='observed'):
        if not self.groq_client:
            return None
        started = time.perf_counter()
        try:
            groq_response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {'role': 'system', 'content': GROQ_JSON_PROMPT},
                    {'role': 'user', 'content': user_content}
                ],
                response_format={'type': 'json_object'},
                temperature=0.2
            )
        except Exception as e:
            record_api_call(
                request_id=request_id,
                modality=modality,
                provider='groq',
                model=GROQ_MODEL,
                operation='chat_completion',
                status='error',
                latency_ms=(time.perf_counter() - started) * 1000,
                sample_type=sample_type,
                error_type=type(e).__name__,
            )
            print(f'Fallback Groq com {GROQ_MODEL} falhou: {e}')
            return None

        usage = groq_response.usage
        record_api_call(
            request_id=request_id,
            modality=modality,
            provider='groq',
            model=GROQ_MODEL,
            operation='chat_completion',
            status='success',
            input_tokens=getattr(usage, 'prompt_tokens', None),
            output_tokens=getattr(usage, 'completion_tokens', None),
            latency_ms=(time.perf_counter() - started) * 1000,
            sample_type=sample_type,
        )
        try:
            report_dict = self._normalize_actions(
                json.loads(groq_response.choices[0].message.content)
            )
            return DiagnosticReport(**report_dict)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            print(f'Resposta Groq inválida para o esquema: {type(error).__name__}')
            return None

    def _generate_gemini(self, contents, request_id, modality):
        if not self.client:
            return None

        for model_name in dict.fromkeys(self.fallback_models):
            for attempt in range(2):
                started = time.perf_counter()
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
                except Exception as e:
                    record_api_call(
                        request_id=request_id,
                        modality=modality,
                        provider='gemini',
                        model=model_name,
                        operation='generate_content',
                        status='error',
                        latency_ms=(time.perf_counter() - started) * 1000,
                        error_type=type(e).__name__,
                    )
                    print(f'Tentativa {attempt + 1} com {model_name} falhou: {e}')
                    if attempt == 0:
                        time.sleep(2)
                    continue

                usage = getattr(response, 'usage_metadata', None)
                record_api_call(
                    request_id=request_id,
                    modality=modality,
                    provider='gemini',
                    model=model_name,
                    operation='generate_content',
                    status='success',
                    input_tokens=getattr(usage, 'prompt_token_count', None),
                    output_tokens=getattr(usage, 'candidates_token_count', None),
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
                try:
                    return DiagnosticReport(**json.loads(response.text))
                except (json.JSONDecodeError, TypeError, ValueError) as error:
                    print(f'Resposta Gemini inválida para o esquema: {type(error).__name__}')
        return None

    def _generate_cache_key(self, prompt: str, image_path: str = None) -> str:
        content_str = prompt + (image_path if image_path else '')
        return hashlib.sha256(content_str.encode('utf-8')).hexdigest()

    def manual_only_report(self, rag_context: str) -> DiagnosticReport:
        return self._manual_fallback(rag_context)

    def analyze_dashboard_alert(
        self,
        image_path: str,
        context_text: str,
        rag_context: str,
        request_id: str,
        modality: str,
    ) -> DiagnosticReport:
        cache_key = self._generate_cache_key(context_text + rag_context, image_path)
        if cache_key in self.cache:
            print('Retornando resposta do cache local...')
            record_api_call(
                request_id=request_id,
                modality=modality,
                provider='local',
                model='response-cache',
                operation='cache_lookup',
                status='cache_hit',
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
            )
            return self.cache[cache_key]

        user_content = (
            f"{DIAGNOSIS_PROMPT}\n\n"
            f"--- CONTEXTO DO MOTORISTA (Relato/Áudio) ---\n"
            f"{context_text}\n\n"
            f"--- CONTEXTO EXTRAÍDO DO MANUAL TÉCNICO (RAG) ---\n"
            f"{rag_context}\n\n"
            f"Por favor, identifique a luz no painel e forneça a análise completa de acordo com o esquema requerido."
        )

        contents = [user_content]
        if image_path:
            if not os.path.exists(image_path):
                raise LLMProviderError('O arquivo da imagem não está mais disponível. Envie a foto novamente.')
            try:
                with Image.open(image_path) as image:
                    image.verify()
                with Image.open(image_path) as image:
                    image.load()
                    img = image.copy()
            except OSError as error:
                raise LLMProviderError('O arquivo enviado não é uma imagem válida. Envie outra foto.') from error
            contents.append(img)

        if image_path:
            try:
                report = self._generate_gemini(contents, request_id, modality)
            finally:
                img.close()
            if not report:
                raise LLMProviderError(
                    'Não foi possível analisar a imagem porque o Gemini está indisponível. '
                    'A foto não foi processada; tente novamente mais tarde.'
                )
        else:
            providers = ('groq', 'gemini') if PROVEDOR == 'groq' else ('gemini', 'groq')
            report = None
            for provider in providers:
                if provider == 'groq':
                    report = self._generate_groq(user_content, request_id, modality)
                else:
                    report = self._generate_gemini(contents, request_id, modality)
                if report:
                    break

            if not report:
                raise LLMProviderError(
                    'Os provedores de IA estão indisponíveis. Consulte os trechos recuperados '
                    'do manual ou tente novamente mais tarde.'
                )

        self.cache[cache_key] = report
        return report

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
