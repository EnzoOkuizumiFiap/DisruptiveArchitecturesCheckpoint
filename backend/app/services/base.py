"""
Contratos e Interfaces Abstratas (SOLID - OCP, LSP, ISP, DIP)
Permite trocar ou simular provedores de IA e motores de busca sem modificar a lógica de negócios.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Protocol, runtime_checkable


class BaseAIProvider(ABC):
    """Contrato base para provedores de IA Generativa e Embeddings."""

    @abstractmethod
    def embed_query(self, query: str) -> Optional[List[float]]:
        """Gera embedding para a query de busca."""
        pass

    @abstractmethod
    def generate_answer(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Gera resposta fundamentada usando o contexto recuperado e histórico de chat."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Indica se o provedor está devidamente autenticado e operacional."""
        pass


@runtime_checkable
class BaseRetriever(Protocol):
    """Protocolo comum para motores de recuperação de documentos (BM25, Vetorial)."""

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Retorna lista de tuplas (índice_documento, score_relevância)."""
        ...


@runtime_checkable
class BaseSessionManager(Protocol):
    """Protocolo para gerenciadores de sessão de chat."""

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        ...

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict]] = None,
        latency_ms: Optional[float] = None
    ) -> None:
        ...

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        ...

    def get_session_detail(self, session_id: str) -> Optional[Dict]:
        ...

    def list_sessions(self) -> List[Dict]:
        ...

    def update_title(self, session_id: str, new_title: str) -> bool:
        ...

    def clear_session(self, session_id: str) -> bool:
        ...
