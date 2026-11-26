import argparse
import csv
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = PROJECT_ROOT / 'logs' / 'usage.csv'


def estimate_monthly_cost(rows, users=50, queries_per_day=10, days=30):
    requests = {}
    synthetic_requests = set()
    for row in rows:
        request_id = row.get('request_id')
        modality = row.get('modality')
        if not request_id or not modality:
            raise ValueError('Cada registro precisa de request_id e modality.')
        if row.get('sample_type') == 'synthetic':
            synthetic_requests.add(request_id)
            continue

        request = requests.setdefault(
            request_id,
            {
                'modality': modality,
                'cost': 0.0,
                'complete': True,
                'has_observed_call': False,
            },
        )
        if request['modality'] != modality:
            raise ValueError(f'Modalidade inconsistente para request_id {request_id}.')

        if row.get('status') == 'request_started':
            continue
        request['has_observed_call'] = True
        cost = row.get('estimated_cost_usd', '')
        if row.get('status') == 'cache_hit':
            continue
        if cost in (None, ''):
            request['complete'] = False
        else:
            request['cost'] += float(cost)

    by_modality = defaultdict(list)
    for request in requests.values():
        by_modality[request['modality']].append(request)

    monthly_requests = users * queries_per_day * days
    result = {
        'sample_requests': len(requests),
        'synthetic_requests_excluded': len(synthetic_requests),
        'monthly_requests': monthly_requests,
        'modalities': {},
        'projected_monthly_cost_usd': 0.0,
    }
    complete_counts = [
        sum(
            request['complete'] and request['has_observed_call']
            for request in modality_requests
        )
        for modality_requests in by_modality.values()
    ]
    result['preliminary'] = bool(requests) and min(complete_counts, default=0) < 5

    projection_complete = bool(requests)
    for modality, modality_requests in sorted(by_modality.items()):
        complete = [
            request for request in modality_requests
            if request['complete'] and request['has_observed_call']
        ]
        incomplete_count = len(modality_requests) - len(complete)
        share = len(modality_requests) / len(requests)
        average_cost = (
            sum(request['cost'] for request in complete) / len(complete)
            if complete else None
        )
        projected_cost = (
            average_cost * monthly_requests * share
            if average_cost is not None else None
        )
        if projected_cost is None:
            projection_complete = False
        else:
            result['projected_monthly_cost_usd'] += projected_cost

        result['modalities'][modality] = {
            'sample_requests': len(modality_requests),
            'complete_requests': len(complete),
            'incomplete_requests': incomplete_count,
            'observed_share': share,
            'average_cost_usd': average_cost,
            'projected_monthly_cost_usd': projected_cost,
        }

    if not projection_complete:
        result['projected_monthly_cost_usd'] = None
    return result


def load_rows(log_path):
    with Path(log_path).open(encoding='utf-8', newline='') as csv_file:
        return list(csv.DictReader(csv_file))


def main():
    parser = argparse.ArgumentParser(
        description='Projeta o custo mensal a partir do CSV local de uso das APIs.'
    )
    parser.add_argument('--log', type=Path, default=DEFAULT_LOG)
    parser.add_argument('--users', type=int, default=50)
    parser.add_argument('--queries-per-day', type=int, default=10)
    parser.add_argument('--days', type=int, default=30)
    args = parser.parse_args()

    if min(args.users, args.queries_per_day, args.days) <= 0:
        parser.error('users, queries-per-day e days precisam ser maiores que zero.')
    if not args.log.is_file():
        parser.error(f'Log não encontrado: {args.log}. Execute análises primeiro.')

    estimate = estimate_monthly_cost(
        load_rows(args.log),
        users=args.users,
        queries_per_day=args.queries_per_day,
        days=args.days,
    )
    print(f"Solicitações observadas: {estimate['sample_requests']}")
    print(f"Solicitações sintéticas excluídas: {estimate['synthetic_requests_excluded']}")
    print(f"Solicitações no cenário: {estimate['monthly_requests']}")
    if estimate['preliminary']:
        print('Atenção: amostra preliminar (menos de 5 solicitações completas em ao menos uma modalidade).')
    print('Mix observado e projeção por modalidade:')
    for modality, values in estimate['modalities'].items():
        average = values['average_cost_usd']
        projected = values['projected_monthly_cost_usd']
        average_text = 'indisponível' if average is None else f'US$ {average:.6f}'
        projected_text = 'indisponível' if projected is None else f'US$ {projected:.2f}'
        print(
            f"- {modality}: {values['observed_share']:.1%} do mix; "
            f"{values['complete_requests']}/{values['sample_requests']} registros "
            f"completos; média {average_text}; projeção {projected_text}"
        )

    total = estimate['projected_monthly_cost_usd']
    if total is None:
        print('Projeção total indisponível: falta amostra completa para uma modalidade.')
    else:
        print(f'Projeção mensal estimada: US$ {total:.2f}')


if __name__ == '__main__':
    main()
