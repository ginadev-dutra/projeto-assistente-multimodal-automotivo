import csv
from datetime import date, datetime, timezone
from pathlib import Path
from threading import Lock


ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / 'logs' / 'usage.csv'
FIELDS = [
    'timestamp_utc',
    'request_id',
    'sample_type',
    'modality',
    'provider',
    'model',
    'operation',
    'status',
    'input_tokens',
    'output_tokens',
    'audio_seconds',
    'latency_ms',
    'estimated_cost_usd',
    'cost_basis',
    'error_type',
]
_LOG_LOCK = Lock()


def _gemini_rates(model):
    if model == 'gemini-3.1-flash-lite':
        return 0.25, 1.50, 'Google list pricing'
    if model == 'gemini-3.8-flash':
        if date.today() <= date(2026, 12, 31):
            return 0.75, 3.75, 'Google list pricing through 2026-12-31'
        return 1.50, 7.50, 'Google list pricing from 2027-01-01'
    return None


def estimate_call_cost(
    provider,
    model,
    input_tokens=None,
    output_tokens=None,
    audio_seconds=None,
):
    if provider == 'gemini':
        rates = _gemini_rates(model)
        if rates is None or input_tokens is None or output_tokens is None:
            return '', 'rate_or_usage_unavailable'
        input_rate, output_rate, basis = rates
        cost = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
        return f'{cost:.10f}', basis

    if provider == 'groq' and model == 'openai/gpt-oss-20b':
        if input_tokens is None or output_tokens is None:
            return '', 'usage_unavailable'
        cost = (input_tokens * 0.075 + output_tokens * 0.30) / 1_000_000
        return f'{cost:.10f}', 'Groq list pricing per 1M tokens'

    if provider == 'groq' and model == 'whisper-large-v3-turbo':
        if audio_seconds is None:
            return '', 'audio_duration_unavailable'
        return f'{audio_seconds * 0.04 / 3600:.10f}', 'Groq list pricing per audio hour'

    return '', 'rate_unconfigured'


def record_api_call(
    *,
    request_id,
    modality,
    provider,
    model,
    operation,
    status,
    latency_ms,
    sample_type='observed',
    input_tokens=None,
    output_tokens=None,
    audio_seconds=None,
    error_type='',
):
    estimated_cost, cost_basis = estimate_call_cost(
        provider,
        model,
        input_tokens,
        output_tokens,
        audio_seconds,
    )
    row = {
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'request_id': request_id,
        'sample_type': sample_type,
        'modality': modality,
        'provider': provider,
        'model': model,
        'operation': operation,
        'status': status,
        'input_tokens': '' if input_tokens is None else input_tokens,
        'output_tokens': '' if output_tokens is None else output_tokens,
        'audio_seconds': '' if audio_seconds is None else audio_seconds,
        'latency_ms': round(latency_ms, 2),
        'estimated_cost_usd': estimated_cost,
        'cost_basis': cost_basis,
        'error_type': error_type,
    }

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_LOCK:
        write_header = not LOG_PATH.exists() or LOG_PATH.stat().st_size == 0
        with LOG_PATH.open('a', encoding='utf-8', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(row)


def record_request_start(request_id, modality, sample_type='observed'):
    record_api_call(
        request_id=request_id,
        modality=modality,
        provider='local',
        model='diagnosis-request',
        operation='request_start',
        status='request_started',
        latency_ms=0,
        sample_type=sample_type,
    )
