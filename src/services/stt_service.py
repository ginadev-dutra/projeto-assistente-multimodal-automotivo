import os
from openai import OpenAI
from src.config import GROQ_API_KEY

class STTService:
    def __init__(self):
        self.groq_client = OpenAI(api_key=GROQ_API_KEY, base_url='https://api.groq.com/openai/v1') if GROQ_API_KEY else None

    def transcribe_audio(self, audio_path: str) -> str:
        if not audio_path or not os.path.exists(audio_path):
            return ''
        if self.groq_client:
            try:
                with open(audio_path, 'rb') as audio_file:
                    transcript = self.groq_client.audio.transcriptions.create(
                        file=audio_file,
                        model='whisper-large-v3-turbo',
                        language='pt'
                    )
                    return transcript.text
            except Exception as e:
                print(f'Erro no Whisper Groq: {e}')
        return '[Áudio recebido, mas chave Groq não configurada. Prosseguindo com contexto textual.]'
