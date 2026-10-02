"""
Esquemas de Dados e DTOs (Pydantic)
Clean Code & DRY: Modelos tipados e validados para toda a aplicação.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    title: str = Field(..., description="Título da seção ou documento de referência")
    url: str = Field(..., description="URL canônica no MkDocs da disciplina")
    category: Optional[str] = Field("", description="Categoria temática (ex: IoT, GenAI, Checkpoint)")


class SearchResult(BaseModel):
    chunk_id: str
    title: str
    category: str
    url: str
    content: str
    rrf_score: float = Field(..., description="Pontuação combinada Reciprocal Rank Fusion")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Dúvida ou comando do usuário")
    session_id: Optional[str] = Field(None, description="Identificador único da sessão para memória conversacional")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Resposta fundamentada do assistente")
    sources: List[SourceItem] = Field(default_factory=list, description="Lista de links e páginas consultadas")
    session_id: str = Field(..., description="Identificador da sessão ativa")
    latency_ms: float = Field(..., description="Tempo de resposta em milissegundos")


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchResult]


class HealthResponse(BaseModel):
    status: str
    version: str
    chunks_count: int
    bm25_ready: bool
    vectors_ready: bool
    ai_provider_configured: bool


class MessageDetail(BaseModel):
    role: str
    content: str
    sources: Optional[List[SourceItem]] = Field(default_factory=list)
    latency_ms: Optional[float] = None
    timestamp: float


class SessionSummary(BaseModel):
    id: str
    title: str
    created_at: float
    last_active: float
    message_count: int


class SessionDetailResponse(BaseModel):
    id: str
    title: str
    created_at: float
    last_active: float
    messages: List[MessageDetail]


class UpdateTitleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)


class ClearSessionResponse(BaseModel):
    session_id: str
    cleared: bool
    message: str
