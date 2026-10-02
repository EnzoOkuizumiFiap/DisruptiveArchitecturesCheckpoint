"""
Motor de Busca Vetorial com NumPy e Similaridade de Cosseno L2 Normalizada
"""

from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

from app.core.config import settings
from app.core.logging import logger


class VectorStore:
    """Repositório de vetores em memória com normalização L2 pré-computada."""

    def __init__(self, embeddings_path: Optional[Path] = None):
        self.embeddings_path = embeddings_path or settings.EMBEDDINGS_PATH
        self.vectors: Optional[np.ndarray] = None
        self.normalized_vectors: Optional[np.ndarray] = None
        self.dim: int = 0
        self.load()

    def load(self) -> bool:
        """Carrega e normaliza os vetores pré-computados se existirem."""
        if self.embeddings_path and self.embeddings_path.exists():
            try:
                self.vectors = np.load(str(self.embeddings_path)).astype(np.float32)
                norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1e-10
                self.normalized_vectors = self.vectors / norms
                self.dim = self.vectors.shape[1]
                logger.info(f"VectorStore carregado: {self.vectors.shape[0]} vetores (dimensão: {self.dim})")
                return True
            except Exception as err:
                logger.error(f"Erro ao carregar matriz de embeddings de {self.embeddings_path}: {err}")
        else:
            logger.info(f"Arquivo de embeddings não localizado em {self.embeddings_path}. Operando via fallback BM25.")
        return False

    def is_available(self) -> bool:
        """Verifica se há vetores normalizados carregados."""
        return self.normalized_vectors is not None and len(self.normalized_vectors) > 0

    def search_vector(self, query_vector: List[float], top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Calcula a similaridade de cosseno via produto escalar com os vetores normalizados.
        Retorna lista ordenada de tuplas (índice, score).
        """
        if not self.is_available() or not query_vector:
            return []

        q = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q_unit = q / q_norm

        similarities = np.dot(self.normalized_vectors, q_unit)
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(int(idx), float(similarities[idx])) for idx in top_indices if similarities[idx] > 0]
