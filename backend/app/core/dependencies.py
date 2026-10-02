"""
Provedores de Injeção de Dependência para FastAPI (SOLID - DIP)
Permite desacoplar as rotas dos serviços concretos e facilita testes unitários e mocks.
"""

from app.services.base import BaseAIProvider, BaseSessionManager
from app.services.gemini import get_ai_provider as _get_ai_provider
from app.services.rag_engine import rag_engine as _rag_engine, RAGEngine
from app.services.memory import memory_manager as _memory_manager


def get_ai_provider() -> BaseAIProvider:
    """Injeta a instância ativa do provedor de IA (Gemini ou Mock)."""
    return _get_ai_provider()


def get_rag_engine() -> RAGEngine:
    """Injeta a instância ativa do motor RAG híbrido."""
    return _rag_engine


def get_memory_manager() -> BaseSessionManager:
    """Injeta a instância ativa do gerenciador de sessões."""
    return _memory_manager
