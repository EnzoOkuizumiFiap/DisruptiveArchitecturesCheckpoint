"""
Motor Léxico BM25 Okapi em Python Puro
Clean Code & Performance: Implementação otimizada sem bibliotecas C externas.
"""

import math
import re
from collections import Counter
from typing import List, Dict, Tuple


def tokenizar(texto: str) -> List[str]:
    """Tokeniza texto em palavras minúsculas, preservando termos técnicos de IoT/IA."""
    if not texto:
        return []
    texto = texto.lower()
    return re.findall(r"\b[a-z0-9_\-\+]{2,}\b", texto)


class BM25Okapi:
    """Implementação do algoritmo Okapi BM25 com Índice Invertido de Alta Performance."""

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / max(self.corpus_size, 1)
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []
        # Índice Invertido: token -> lista de (doc_index, term_frequency)
        self.inverted_index: Dict[str, List[Tuple[int, int]]] = {}

        self._build_index(corpus)

    def _build_index(self, corpus: List[List[str]]):
        df_counts = Counter()
        for doc_idx, doc in enumerate(corpus):
            self.doc_len.append(len(doc))
            frequencies = Counter(doc)
            for token, tf in frequencies.items():
                df_counts[token] += 1
                if token not in self.inverted_index:
                    self.inverted_index[token] = []
                self.inverted_index[token].append((doc_idx, tf))

        for token, freq in df_counts.items():
            # Fórmula IDF com amortecimento de Okapi
            self.idf[token] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        """
        Calcula o score BM25 utilizando o índice invertido O(postings).
        Garante desempenho sub-milissegundo sem iterar sobre documentos irrelevantes.
        """
        scores = [0.0] * self.corpus_size
        k1 = self.k1
        b = self.b
        avgdl = self.avgdl

        for token in query_tokens:
            if token not in self.idf or token not in self.inverted_index:
                continue
            idf_val = self.idf[token]
            postings = self.inverted_index[token]

            for doc_idx, tf in postings:
                d_len = self.doc_len[doc_idx]
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (d_len / avgdl))
                scores[doc_idx] += idf_val * (numerator / denominator)

        return scores

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Retorna lista de (doc_index, score) ordenada pelos maiores scores."""
        query_tokens = tokenizar(query)
        if not query_tokens:
            return []
        scores = self.get_scores(query_tokens)
        scored_docs = [(i, score) for i, score in enumerate(scores) if score > 0]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:top_k]
