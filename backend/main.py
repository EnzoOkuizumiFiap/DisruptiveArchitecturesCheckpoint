"""
Ponto de Entrada da Aplicação FastAPI
Modern FastAPI com Lifespan Context Manager, CORS, Exception Handlers e UI estática.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import register_exception_handlers
from app.api.routes import router as api_router
from app.services.rag_engine import rag_engine
from app.services.gemini import get_ai_provider

STATIC_DIR = Path(__file__).parent / "app" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento do ciclo de vida da aplicação (startup e shutdown)."""
    ai = get_ai_provider()
    logger.info("==================================================")
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📚 Base de Conhecimento: {len(rag_engine.chunks)} chunks ativos")
    logger.info(f"🔎 Motor BM25: {'Operacional' if rag_engine.bm25 else 'Inativo'}")
    logger.info(f"🧠 Motor Vetorial: {'Operacional' if rag_engine.vector_store and rag_engine.vector_store.is_available() else 'Fallback BM25'}")
    logger.info(f"🤖 Provedor IA: {'Gemini Conectado' if ai.is_configured() else 'Modo Mock/Fallback'}")
    logger.info("==================================================")
    yield
    logger.info("Encerrando serviços do RAG Assistant...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API RAG Híbrida (Vetorial + BM25) para a disciplina Disruptive Architectures: IA e IoT",
    lifespan=lifespan
)

# Registra tratamento padronizado de exceções
register_exception_handlers(app)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montagem de estáticos
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/chat", response_class=HTMLResponse, summary="Interface Web do Chat")
async def serve_chat_page():
    """Serve a interface gráfica web para navegação e testes."""
    chat_file = STATIC_DIR / "chat.html"
    if chat_file.exists():
        return FileResponse(str(chat_file))
    return HTMLResponse("<h1>Interface não encontrada</h1>", status_code=404)


@app.get("/widget.js", summary="Script JS do Widget Flutuante")
async def serve_widget_js():
    """Serve o script do widget flutuante para injeção no MkDocs."""
    widget_file = STATIC_DIR / "widget.js"
    if widget_file.exists():
        return FileResponse(str(widget_file), media_type="application/javascript")
    return HTMLResponse("// widget não encontrado", status_code=404)


# Rotas da API
app.include_router(api_router, prefix="/api", tags=["RAG Assistant"])


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
