import os
from pypdf import PdfReader
import chromadb

class RAGService:
    def __init__(self, manuals_dir: str = 'manuals'):
        self.manuals_dir = manuals_dir
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(name='manuals_vectorstore')
        self.indexed = False

    def index_manuals(self):
        if not os.path.exists(self.manuals_dir):
            os.makedirs(self.manuals_dir, exist_ok=True)
            return
        
        documents = []
        metadatas = []
        ids = []
        doc_count = 0

        for file in os.listdir(self.manuals_dir):
            if file.endswith('.pdf'):
                path = os.path.join(self.manuals_dir, file)
                reader = PdfReader(path)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        doc_count += 1
                        documents.append(text)
                        metadatas.append({'source': file, 'page': i + 1})
                        ids.append(f'{file}_p{i+1}')
        
        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
            self.indexed = True
            print(f'RAG Indexado com sucesso: {doc_count} páginas de manuais.')

    def search_manual(self, query: str, top_k: int = 3) -> str:
        if not self.indexed:
            self.index_manuals()
        if not self.indexed:
            return 'Nenhum manual técnico indexado na pasta /manuals.'
        
        results = self.collection.query(query_texts=[query], n_results=top_k)
        retrieved_texts = []
        if results and 'documents' in results and results['documents']:
            for doc_list, meta_list in zip(results['documents'], results['metadatas']):
                for doc, meta in zip(doc_list, meta_list):
                    retrieved_texts.append(
                        f"[Fonte: {meta['source']} - Pág. {meta['page']}]\n{doc}"
                    )
        return '\n\n---\n\n'.join(retrieved_texts)
