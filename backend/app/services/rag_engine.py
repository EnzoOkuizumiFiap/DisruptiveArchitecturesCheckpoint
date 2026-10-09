"""
Motor RAG Híbrido: Recuperação Semântica + Léxica com Fusão RRF (Reciprocal Rank Fusion)
Clean Code: Separação de responsabilidades (SRP) entre busca, fusão e montagem de contexto.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import KnowledgeBaseNotFoundError
from app.models.schemas import SearchResult, SourceItem
from app.services.bm25 import BM25Okapi, tokenizar
from app.services.vector_store import VectorStore


class RAGEngine:
    """Motor de recuperação e orquestração de conhecimento para o assistente."""

    def __init__(
        self,
        knowledge_path: Optional[Path] = None,
        embeddings_path: Optional[Path] = None
    ):
        self.knowledge_path = knowledge_path or settings.KNOWLEDGE_BASE_PATH
        self.embeddings_path = embeddings_path or settings.EMBEDDINGS_PATH
        self.chunks: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None
        self.vector_store: Optional[VectorStore] = None
        self._initialize()

    def _initialize(self):
        """Carrega os chunks e inicializa os motores de busca."""
        if not self.knowledge_path.exists():
            logger.warning(f"Arquivo de base de dados não encontrado em: {self.knowledge_path}")
            return

        try:
            self.chunks = json.loads(self.knowledge_path.read_text(encoding="utf-8-sig"))
            logger.info(f"RAGEngine: {len(self.chunks)} chunks carregados da base de conhecimento.")

            # Inicializa motor léxico BM25
            corpus_tokens = [
                tokenizar(c.get("content", "") + " " + c.get("title", ""))
                for c in self.chunks
            ]
            self.bm25 = BM25Okapi(corpus_tokens)
            logger.info("RAGEngine: Índice BM25 inicializado com sucesso.")

            # Inicializa motor vetorial
            self.vector_store = VectorStore(self.embeddings_path)

        except Exception as err:
            logger.error(f"Erro ao inicializar RAGEngine: {err}", exc_info=True)
            raise KnowledgeBaseNotFoundError(str(self.knowledge_path)) from err

    def search_hybrid(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        top_k: int = 5,
        rrf_k: int = 60
    ) -> List[SearchResult]:
        """
        Executa recuperação híbrida combinando BM25 e Similaridade Vetorial via RRF.
        RRF_Score(d) = sum( weight / (k + rank(d)) )
        """
        if not self.chunks:
            return []

        # 1. Recuperação BM25
        bm25_matches = self.bm25.search(query, top_k=top_k * 3) if self.bm25 else []

        # 2. Recuperação Vetorial
        vec_matches = []
        if self.vector_store and self.vector_store.is_available() and query_vector:
            vec_matches = self.vector_store.search_vector(query_vector, top_k=top_k * 3)

        # 3. Fusão RRF
        rrf_scores: Dict[int, float] = {}

        for rank, (doc_idx, _) in enumerate(bm25_matches):
            weight = settings.BM25_WEIGHT
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (weight / (rrf_k + rank + 1))

        for rank, (doc_idx, _) in enumerate(vec_matches):
            weight = settings.VECTOR_WEIGHT
            rrf_scores[doc_idx] = rrf_scores.get(doc_idx, 0.0) + (weight / (rrf_k + rank + 1))

        # Se nenhum vetor estava disponível (modo fallback), usa o BM25
        if not vec_matches and bm25_matches:
            for rank, (doc_idx, score) in enumerate(bm25_matches):
                rrf_scores[doc_idx] = score

        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        results = []
        for doc_idx, score in sorted_docs:
            chunk = self.chunks[doc_idx]
            results.append(SearchResult(
                chunk_id=chunk.get("id", f"chunk_{doc_idx}"),
                title=chunk.get("title", ""),
                category=chunk.get("category", "Geral"),
                url=chunk.get("url", ""),
                content=chunk.get("content", ""),
                rrf_score=float(score)
            ))

        return results

    def build_context_prompt(self, results: List[SearchResult]) -> str:
        """Monta o bloco de contexto estruturado para o prompt do modelo generativo."""
        if not results:
            return "Nenhum documento relevante encontrado no material oficial da disciplina."

        blocks = []
        for i, item in enumerate(results, 1):
            block = (
                f"--- FONTE [{i}]: {item.title} ---\n"
                f"Categoria: {item.category}\n"
                f"URL de Referência: {item.url}\n\n"
                f"{item.content}\n"
            )
            blocks.append(block)

        return "\n".join(blocks)

    def extract_sources(self, results: List[SearchResult]) -> List[SourceItem]:
        """Extrai lista de links e títulos únicos das fontes consultadas."""
        seen_urls = set()
        sources = []
        for r in results:
            if r.url and r.url not in seen_urls:
                seen_urls.add(r.url)
                sources.append(SourceItem(
                    title=r.title,
                    url=r.url,
                    category=r.category
                ))
        return sources


# Instância global singleton do RAGEngine
rag_engine = RAGEngine()
