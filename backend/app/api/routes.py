"""
Controladores e Endpoints da API FastAPI (Clean Code + DIP)
Utiliza Injeção de Dependências (Depends) e Schemas tipados Pydantic.
"""

import time
from typing import List
from fastapi import APIRouter, Depends, Query, status

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import SessionNotFoundError
from app.core.dependencies import get_ai_provider, get_rag_engine, get_memory_manager
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    SearchResponse,
    HealthResponse,
    ClearSessionResponse,
    SessionSummary,
    SessionDetailResponse,
    UpdateTitleRequest
)
from app.services.base import BaseAIProvider, BaseSessionManager
from app.services.rag_engine import RAGEngine

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Interação conversacional com RAG híbrido",
    status_code=status.HTTP_200_OK
)
async def chat_endpoint(
    payload: ChatRequest,
    ai_provider: BaseAIProvider = Depends(get_ai_provider),
    rag: RAGEngine = Depends(get_rag_engine),
    memory: BaseSessionManager = Depends(get_memory_manager)
):
    """
    Recebe a pergunta do aluno, executa a busca híbrida (BM25 + Vetorial),
    gerencia o histórico da sessão e gera a resposta fundamentada com o Gemini.
    """
    start_time = time.perf_counter()
    pergunta = payload.message.strip()
    session_id = memory.get_or_create_session(payload.session_id)

    logger.info(f"Chat request recebido [Session: {session_id[:8]}...]: '{pergunta[:50]}'")

    # 1. Recuperação Híbrida
    query_vector = ai_provider.embed_query(pergunta)
    resultados = rag.search_hybrid(
        query=pergunta,
        query_vector=query_vector,
        top_k=settings.TOP_K_RESULTS
    )

    # 2. Montagem de Contexto e Extração de Fontes
    contexto = rag.build_context_prompt(resultados)
    fontes = rag.extract_sources(resultados)

    # 3. Histórico e Geração com LLM
    historico = memory.get_history(session_id)
    resposta = ai_provider.generate_answer(
        question=pergunta,
        context=contexto,
        conversation_history=historico
    )

    # 4. Atualização de Memória com fontes e latência para reconstituição de histórico
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    fontes_dicts = [f.model_dump() for f in fontes]

    memory.add_message(session_id, "user", pergunta)
    memory.add_message(
        session_id,
        "model",
        resposta,
        sources=fontes_dicts,
        latency_ms=round(elapsed_ms, 2)
    )

    return ChatResponse(
        answer=resposta,
        sources=fontes,
        session_id=session_id,
        latency_ms=round(elapsed_ms, 2)
    )


@router.get(
    "/chat/sessions",
    response_model=List[SessionSummary],
    summary="Listar histórico de conversas do usuário"
)
async def list_sessions_endpoint(
    memory: BaseSessionManager = Depends(get_memory_manager)
):
    """Retorna todas as conversas salvas ordenadas pela mais recente para a barra lateral."""
    return memory.list_sessions()


@router.get(
    "/chat/session/{session_id}",
    response_model=SessionDetailResponse,
    summary="Carregar histórico completo de uma conversa"
)
async def get_session_endpoint(
    session_id: str,
    memory: BaseSessionManager = Depends(get_memory_manager)
):
    """Recupera todas as mensagens, fontes e detalhes de uma conversa específica."""
    detail = memory.get_session_detail(session_id)
    if not detail:
        raise SessionNotFoundError(session_id)
    return detail


@router.patch(
    "/chat/session/{session_id}/title",
    summary="Renomear título de uma conversa"
)
async def update_session_title_endpoint(
    session_id: str,
    payload: UpdateTitleRequest,
    memory: BaseSessionManager = Depends(get_memory_manager)
):
    """Permite renomear o título exibido na barra lateral para a conversa."""
    sucesso = memory.update_title(session_id, payload.title)
    if not sucesso:
        raise SessionNotFoundError(session_id)
    return {"session_id": session_id, "title": payload.title, "updated": True}


@router.delete(
    "/chat/session/{session_id}",
    response_model=ClearSessionResponse,
    summary="Excluir uma conversa específica"
)
async def clear_session_endpoint(
    session_id: str,
    memory: BaseSessionManager = Depends(get_memory_manager)
):
    """Exclui permanentemente o histórico de uma conversa."""
    sucesso = memory.clear_session(session_id)
    return ClearSessionResponse(
        session_id=session_id,
        cleared=sucesso,
        message="Conversa excluída com sucesso." if sucesso else "Sessão não existia ou já estava vazia."
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Auditoria e teste de recuperação híbrida"
)
async def search_endpoint(
    q: str = Query(..., min_length=1, description="Termo ou pergunta técnica"),
    top_k: int = Query(5, ge=1, le=20, description="Quantidade de chunks a retornar"),
    ai_provider: BaseAIProvider = Depends(get_ai_provider),
    rag: RAGEngine = Depends(get_rag_engine)
):
    """Permite testar e inspecionar os scores da busca híbrida sem acionar o LLM."""
    query_vector = ai_provider.embed_query(q)
    resultados = rag.search_hybrid(
        query=q,
        query_vector=query_vector,
        top_k=top_k
    )
    return SearchResponse(
        query=q,
        total_results=len(resultados),
        results=resultados
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check dos motores RAG e Provedor de IA"
)
async def health_endpoint(
    ai_provider: BaseAIProvider = Depends(get_ai_provider),
    rag: RAGEngine = Depends(get_rag_engine)
):
    """Verifica o status de prontidão da API e dos componentes de busca."""
    vectors_ready = rag.vector_store.is_available() if rag.vector_store else False
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        chunks_count=len(rag.chunks),
        bm25_ready=rag.bm25 is not None,
        vectors_ready=vectors_ready,
        ai_provider_configured=ai_provider.is_configured()
    )
