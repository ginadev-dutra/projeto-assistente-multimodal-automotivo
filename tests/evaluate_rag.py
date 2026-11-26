import json
import math
import re
import unicodedata
from pathlib import Path

import chromadb

from src.services.rag_service import RAGService


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = ROOT / 'dados' / 'exemplos' / 'perguntas_rag.json'
RRF_CANDIDATES = 10
RRF_CONSTANT = 60
PAGE_WINDOW_SIZES = (2, 3)
BM25_K1 = 1.5
BM25_B = 0.75
STOP_WORDS = set(
    'a ao aos as com como da das de do dos e em entre essa esse esta este eu '
    'foi isso na nas no nos num numa o os ou para pela pelas pelo pelos pode '
    'por qual quando que se sem sua suas tem um uma voce'.split()
)


def normalize_tokens(text):
    normalized = unicodedata.normalize('NFKD', text.casefold())
    normalized = ''.join(char for char in normalized if not unicodedata.combining(char))
    return re.findall(r'(?u)\b\w+\b', normalized)


def build_keyword_query(question):
    words = normalize_tokens(question)
    return ' '.join(word for word in words if word not in STOP_WORDS and len(word) > 2)


def reciprocal_rank_fusion(*ranked_results):
    scores = {}
    metadata_by_page = {}
    for results in ranked_results:
        for rank, metadata in enumerate(results, start=1):
            page = metadata['page']
            scores[page] = scores.get(page, 0) + 1 / (RRF_CONSTANT + rank)
            metadata_by_page[page] = metadata
    ordered_pages = sorted(scores, key=scores.get, reverse=True)
    return [metadata_by_page[page] for page in ordered_pages]


def rank_bm25(query, documents, metadatas):
    tokenized_documents = [normalize_tokens(document) for document in documents]
    query_tokens = [
        token for token in normalize_tokens(query)
        if token not in STOP_WORDS and len(token) > 2
    ]
    document_count = len(tokenized_documents)
    if not document_count:
        return []

    document_frequency = {}
    for tokens in tokenized_documents:
        for token in set(tokens):
            document_frequency[token] = document_frequency.get(token, 0) + 1

    average_length = sum(map(len, tokenized_documents)) / document_count
    scores = []
    for metadata, tokens in zip(metadatas, tokenized_documents):
        term_frequency = {}
        for token in tokens:
            term_frequency[token] = term_frequency.get(token, 0) + 1

        score = 0.0
        for token in query_tokens:
            frequency = term_frequency.get(token, 0)
            if not frequency:
                continue
            doc_frequency = document_frequency[token]
            inverse_document_frequency = math.log(
                1 + (document_count - doc_frequency + 0.5) / (doc_frequency + 0.5)
            )
            denominator = frequency + BM25_K1 * (
                1 - BM25_B + BM25_B * len(tokens) / average_length
            )
            score += inverse_document_frequency * (
                frequency * (BM25_K1 + 1) / denominator
            )
        scores.append((score, metadata))

    scores.sort(key=lambda item: item[0], reverse=True)
    return [metadata for score, metadata in scores if score > 0]


def create_page_windows(documents, metadatas, window_size):
    pages_by_source = {}
    for document, metadata in zip(documents, metadatas):
        pages_by_source.setdefault(metadata['source'], []).append((metadata['page'], document))

    window_documents = []
    window_metadatas = []
    window_ids = []
    for source, pages in pages_by_source.items():
        pages.sort(key=lambda item: item[0])
        for start in range(max(0, len(pages) - window_size + 1)):
            window = pages[start:start + window_size]
            if len(window) != window_size:
                continue
            page_numbers = [page for page, _ in window]
            if page_numbers != list(range(page_numbers[0], page_numbers[0] + window_size)):
                continue
            window_documents.append(
                '\n\n'.join(text for _, text in window)
            )
            window_metadatas.append({
                'source': source,
                'start_page': page_numbers[0],
                'end_page': page_numbers[-1]
            })
            window_ids.append(f'{source}:{page_numbers[0]}-{page_numbers[-1]}')
    return window_documents, window_metadatas, window_ids


def main():
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding='utf-8'))
    rag = RAGService(manuals_dir=str(ROOT / 'manuals'))
    rag.index_manuals()

    corpus = rag.collection.get(include=['documents', 'metadatas'])
    documents = corpus['documents']
    corpus_metadatas = corpus['metadatas']
    window_collections = {}
    window_hits = {window_size: 0 for window_size in PAGE_WINDOW_SIZES}
    for window_size in PAGE_WINDOW_SIZES:
        window_documents, window_metadatas, window_ids = create_page_windows(
            documents, corpus_metadatas, window_size
        )
        window_collection = chromadb.Client().create_collection(
            name=f'rag_page_windows_{window_size}'
        )
        window_collection.add(
            documents=window_documents,
            metadatas=window_metadatas,
            ids=window_ids
        )
        window_collections[window_size] = window_collection

    baseline_hits = keyword_fusion_hits = bm25_fusion_hits = 0
    k = benchmark['k']
    print(
        f"{'ID':<8} {'BASE TOP-K':<20} {'KEYWORD RRF':<20} "
        f"{'BM25 RRF':<20} {'2-PAGE WINDOWS':<20} "
        f"{'3-PAGE WINDOWS':<20} {'EXPECTED':<12}"
    )
    print('-' * 132)

    for case in benchmark['cases']:
        baseline_results = rag.collection.query(
            query_texts=[case['question']],
            n_results=RRF_CANDIDATES,
            include=['metadatas']
        )['metadatas'][0]
        keyword_query = build_keyword_query(case['question'])
        keyword_results = rag.collection.query(
            query_texts=[keyword_query],
            n_results=RRF_CANDIDATES,
            include=['metadatas']
        )['metadatas'][0]
        keyword_fused_results = reciprocal_rank_fusion(baseline_results, keyword_results)
        lexical_results = rank_bm25(case['question'], documents, corpus_metadatas)
        bm25_fused_results = reciprocal_rank_fusion(baseline_results, lexical_results)
        window_results_by_size = {
            window_size: collection.query(
                query_texts=[case['question']],
                n_results=k,
                include=['metadatas']
            )['metadatas'][0]
            for window_size, collection in window_collections.items()
        }

        baseline_pages = [metadata['page'] for metadata in baseline_results[:k]]
        keyword_fused_pages = [metadata['page'] for metadata in keyword_fused_results[:k]]
        bm25_fused_pages = [metadata['page'] for metadata in bm25_fused_results[:k]]
        window_ranges_by_size = {
            window_size: [
                f"{metadata['start_page']}-{metadata['end_page']}"
                for metadata in results
            ]
            for window_size, results in window_results_by_size.items()
        }
        expected = case['expected_pages']
        baseline_hit = any(page in expected for page in baseline_pages)
        keyword_fusion_hit = any(page in expected for page in keyword_fused_pages)
        bm25_fusion_hit = any(page in expected for page in bm25_fused_pages)
        baseline_hits += int(baseline_hit)
        keyword_fusion_hits += int(keyword_fusion_hit)
        bm25_fusion_hits += int(bm25_fusion_hit)
        for window_size, results in window_results_by_size.items():
            window_hits[window_size] += int(any(
                metadata['start_page'] <= page <= metadata['end_page']
                for metadata in results
                for page in expected
            ))
        print(
            f"{case['id']:<8} {str(baseline_pages):<20} "
            f"{str(keyword_fused_pages):<20} {str(bm25_fused_pages):<20} "
            f"{str(window_ranges_by_size[2]):<20} "
            f"{str(window_ranges_by_size[3]):<20} {str(expected):<12}"
        )

    total = len(benchmark['cases'])
    baseline_score = baseline_hits / total if total else 0
    keyword_fusion_score = keyword_fusion_hits / total if total else 0
    bm25_fusion_score = bm25_fusion_hits / total if total else 0
    print(f"\nBaseline acerto@{k}: {baseline_hits}/{total} ({baseline_score:.0%})")
    print(
        f"Keyword + RRF acerto@{k}: {keyword_fusion_hits}/{total} "
        f"({keyword_fusion_score:.0%})"
    )
    print(
        f"BM25 + RRF acerto@{k}: {bm25_fusion_hits}/{total} "
        f"({bm25_fusion_score:.0%})"
    )
    for window_size in PAGE_WINDOW_SIZES:
        window_score = window_hits[window_size] / total if total else 0
        print(
            f"Janelas de {window_size} páginas acerto@{k}: "
            f"{window_hits[window_size]}/{total} ({window_score:.0%})"
        )


if __name__ == '__main__':
    main()
