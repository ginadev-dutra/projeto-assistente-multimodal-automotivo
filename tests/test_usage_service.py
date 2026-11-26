import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.services import usage_service
from tests.estimate_monthly_cost import estimate_monthly_cost


class UsageServiceTests(unittest.TestCase):
    def test_groq_chat_cost_uses_configured_token_rates(self):
        cost, basis = usage_service.estimate_call_cost(
            'groq',
            'openai/gpt-oss-20b',
            input_tokens=1000,
            output_tokens=500,
        )

        self.assertAlmostEqual(float(cost), 0.000225)
        self.assertEqual(basis, 'Groq list pricing per 1M tokens')

    def test_unconfigured_model_cost_is_not_zero(self):
        cost, basis = usage_service.estimate_call_cost(
            'gemini',
            'unconfigured-model',
            input_tokens=100,
            output_tokens=100,
        )

        self.assertEqual(cost, '')
        self.assertEqual(basis, 'rate_or_usage_unavailable')

    def test_gemini_fallback_model_cost_uses_configured_rate(self):
        cost, basis = usage_service.estimate_call_cost(
            'gemini',
            'gemini-3.1-flash-lite',
            input_tokens=4064,
            output_tokens=341,
        )

        self.assertAlmostEqual(float(cost), 0.0015275)
        self.assertEqual(basis, 'Google list pricing')

    def test_audio_cost_uses_duration_in_hours(self):
        cost, basis = usage_service.estimate_call_cost(
            'groq',
            'whisper-large-v3-turbo',
            audio_seconds=3600,
        )

        self.assertAlmostEqual(float(cost), 0.04)
        self.assertEqual(basis, 'Groq list pricing per audio hour')

    def test_usage_log_contains_metadata_but_no_user_content(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / 'usage.csv'
            with patch.object(usage_service, 'LOG_PATH', log_path):
                usage_service.record_api_call(
                    request_id='request-123',
                    modality='text',
                    provider='groq',
                    model='openai/gpt-oss-20b',
                    operation='chat_completion',
                    status='success',
                    input_tokens=100,
                    output_tokens=50,
                    latency_ms=123.456,
                )

            with log_path.open(encoding='utf-8', newline='') as csv_file:
                row = next(csv.DictReader(csv_file))
        self.assertEqual(row['request_id'], 'request-123')
        self.assertEqual(row['input_tokens'], '100')
        self.assertEqual(row['output_tokens'], '50')
        self.assertNotIn('prompt', row)
        self.assertNotIn('user_text', row)

    def test_monthly_projection_uses_observed_mix_and_excludes_incomplete_samples(self):
        rows = [
            {'request_id': 'text-1', 'sample_type': 'observed', 'modality': 'text', 'status': 'success', 'estimated_cost_usd': '0.01'},
            {'request_id': 'text-2', 'sample_type': 'observed', 'modality': 'text', 'status': 'success', 'estimated_cost_usd': '0.03'},
            {'request_id': 'image-1', 'sample_type': 'observed', 'modality': 'image', 'status': 'success', 'estimated_cost_usd': '0.10'},
            {'request_id': 'image-2', 'sample_type': 'observed', 'modality': 'image', 'status': 'error', 'estimated_cost_usd': ''},
            {'request_id': 'synthetic-1', 'sample_type': 'synthetic', 'modality': 'text', 'status': 'success', 'estimated_cost_usd': '0.99'},
        ]

        result = estimate_monthly_cost(rows, users=1, queries_per_day=10, days=10)

        self.assertEqual(result['monthly_requests'], 100)
        self.assertEqual(result['modalities']['text']['observed_share'], 0.5)
        self.assertEqual(result['modalities']['text']['average_cost_usd'], 0.02)
        self.assertEqual(result['modalities']['image']['incomplete_requests'], 1)
        self.assertEqual(result['projected_monthly_cost_usd'], 6.0)
        self.assertEqual(result['synthetic_requests_excluded'], 1)
        self.assertTrue(result['preliminary'])

    def test_request_without_api_call_is_not_assumed_free(self):
        rows = [
            {'request_id': 'text-1', 'modality': 'text', 'status': 'request_started', 'estimated_cost_usd': ''},
        ]

        result = estimate_monthly_cost(rows, users=1, queries_per_day=10, days=10)

        self.assertIsNone(result['projected_monthly_cost_usd'])
        self.assertEqual(result['modalities']['text']['incomplete_requests'], 1)


if __name__ == '__main__':
    unittest.main()
