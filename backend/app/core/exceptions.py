"""
Exceções de Domínio e Handlers Globais para FastAPI
Clean Code: Tratamento padronizado de erros e respostas semânticas.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger


class RAGBaseException(Exception):
    """Exceção base para todas as falhas de domínio do RAG."""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class KnowledgeBaseNotFoundError(RAGBaseException):
    """Lançada quando a base de dados vetorial ou JSON não é encontrada."""
    def __init__(self, path: str):
        super().__init__(
            message=f"Base de conhecimento não encontrada no caminho: {path}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ProviderUnavailableError(RAGBaseException):
    """Lançada quando o provedor de IA (Gemini) falha ou não está configurado."""
    def __init__(self, detail: str = "Provedor de IA indisponível"):
        super().__init__(
            message=detail,
            status_code=status.HTTP_502_BAD_GATEWAY
        )


class SessionNotFoundError(RAGBaseException):
    """Lançada quando uma sessão de chat não é encontrada."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Sessão de conversa '{session_id}' não encontrada ou expirada.",
            status_code=status.HTTP_404_NOT_FOUND
        )


def register_exception_handlers(app: FastAPI):
    """Registra tratadores de exceção customizados no app FastAPI."""
    @app.exception_handler(RAGBaseException)
    async def rag_exception_handler(request: Request, exc: RAGBaseException):
        logger.warning(f"Exceção de Domínio capturada ({exc.__class__.__name__}): {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.__class__.__name__,
                "detail": exc.message,
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Erro inesperado no servidor: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "detail": "Ocorreu um erro interno inesperado no servidor.",
                "path": str(request.url.path)
            }
        )
