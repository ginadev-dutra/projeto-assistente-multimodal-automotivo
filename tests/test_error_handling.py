import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image

from src.services.llm_service import LLMProviderError, MultimodalLLMService
from src.services.stt_service import STTService


class ErrorHandlingTests(unittest.TestCase):
    def test_invalid_image_returns_a_clear_error(self):
        service = MultimodalLLMService.__new__(MultimodalLLMService)
        service.cache = {}

        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_image = Path(temp_dir) / 'not-an-image.jpg'
            invalid_image.write_text('invalid image data', encoding='utf-8')
            with self.assertRaisesRegex(LLMProviderError, 'não é uma imagem válida'):
                service.analyze_dashboard_alert(
                    image_path=str(invalid_image),
                    context_text='',
                    rag_context='',
                    request_id='request-invalid-image',
                    modality='image',
                )

    def test_gemini_outage_returns_a_clear_message_after_retries(self):
        service = MultimodalLLMService.__new__(MultimodalLLMService)
        service.cache = {}
        service.fallback_models = ['test-model']
        service.client = SimpleNamespace(
            models=SimpleNamespace(
                generate_content=Mock(side_effect=RuntimeError('provider unavailable'))
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            image_path = Path(temp_dir) / 'dashboard.png'
            Image.new('RGB', (1, 1)).save(image_path)
            with patch('src.services.llm_service.record_api_call') as record_call, patch(
                'src.services.llm_service.time.sleep'
            ):
                with self.assertRaisesRegex(LLMProviderError, 'Gemini está indisponível'):
                    service.analyze_dashboard_alert(
                        image_path=str(image_path),
                        context_text='',
                        rag_context='',
                        request_id='request-provider-error',
                        modality='image',
                    )

        self.assertEqual(service.client.models.generate_content.call_count, 2)
        self.assertEqual(record_call.call_count, 2)
        self.assertTrue(
            all(call.kwargs['status'] == 'error' for call in record_call.call_args_list)
        )

    def test_transcription_api_error_is_logged_and_returns_fallback_text(self):
        service = STTService.__new__(STTService)
        service.groq_client = SimpleNamespace(
            audio=SimpleNamespace(
                transcriptions=SimpleNamespace(
                    create=Mock(side_effect=RuntimeError('provider unavailable'))
                )
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = Path(temp_dir) / 'sample.wav'
            audio_path.write_bytes(b'audio')
            with patch('src.services.stt_service.record_api_call') as record_call:
                transcript = service.transcribe_audio(
                    str(audio_path),
                    'request-audio-error',
                    'audio',
                )

        self.assertIn('serviço de transcrição está indisponível', transcript)
        record_call.assert_called_once()
        self.assertEqual(record_call.call_args.kwargs['status'], 'error')
        self.assertEqual(record_call.call_args.kwargs['error_type'], 'RuntimeError')


if __name__ == '__main__':
    unittest.main()
