import os
import time
from openai import OpenAI
from src.config import GROQ_API_KEY
from src.services.usage_service import record_api_call

class STTService:
    def __init__(self):
        self.groq_client = OpenAI(api_key=GROQ_API_KEY, base_url='https://api.groq.com/openai/v1') if GROQ_API_KEY else None

    def transcribe_audio(self, audio_path: str, request_id: str, modality: str) -> str:
        if not audio_path or not os.path.exists(audio_path):
            return ''
        if self.groq_client:
            started = time.perf_counter()
            try:
                with open(audio_path, 'rb') as audio_file:
                    transcript = self.groq_client.audio.transcriptions.create(
                        file=audio_file,
                        model='whisper-large-v3-turbo',
                        language='pt',
                        response_format='verbose_json'
                    )
            except Exception as e:
                record_api_call(
                    request_id=request_id,
                    modality=modality,
                    provider='groq',
                    model='whisper-large-v3-turbo',
                    operation='audio_transcription',
                    status='error',
                    latency_ms=(time.perf_counter() - started) * 1000,
                    error_type=type(e).__name__,
                )
                print(f'Erro no Whisper Groq: {e}')
                return '[Áudio não transcrito: o serviço de transcrição está indisponível. Descreva o ocorrido por texto.]'
            else:
                record_api_call(
                    request_id=request_id,
                    modality=modality,
                    provider='groq',
                    model='whisper-large-v3-turbo',
                    operation='audio_transcription',
                    status='success',
                    audio_seconds=getattr(transcript, 'duration', None),
                    latency_ms=(time.perf_counter() - started) * 1000,
                )
                return transcript.text
        return '[Áudio não transcrito: chave Groq não configurada. Descreva o ocorrido por texto.]'
