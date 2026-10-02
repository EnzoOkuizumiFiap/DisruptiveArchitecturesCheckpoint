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
    """Implementação do algoritmo Okapi BM25 conforme a especificação padrão de RI."""

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / max(self.corpus_size, 1)
        self.doc_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []

        self._build_index(corpus)

    def _build_index(self, corpus: List[List[str]]):
        df_counts = Counter()
        for doc in corpus:
            self.doc_len.append(len(doc))
            frequencies = Counter(doc)
            self.doc_freqs.append(frequencies)
            for token in frequencies.keys():
                df_counts[token] += 1

        for token, freq in df_counts.items():
            # Fórmula IDF com amortecimento de Okapi
            self.idf[token] = math.log(1 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        """Calcula o score BM25 de todos os documentos para os tokens da consulta."""
        scores = [0.0] * self.corpus_size
        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for idx, doc_freq in enumerate(self.doc_freqs):
                tf = doc_freq.get(token, 0)
                if tf == 0:
                    continue
                d_len = self.doc_len[idx]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (d_len / self.avgdl))
                scores[idx] += idf_val * (numerator / denominator)
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
