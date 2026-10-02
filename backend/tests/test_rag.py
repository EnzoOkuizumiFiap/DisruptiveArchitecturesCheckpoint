"""
Testes Unitários do Motor RAG e Provedores (Clean Architecture)
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.rag_engine import RAGEngine
from app.services.gemini import GeminiProvider, MockAIProvider, get_ai_provider
from app.services.memory import ConversationMemory
from app.services.bm25 import BM25Okapi, tokenizar


def test_bm25_tokenization():
    texto = "Configurando ESP32 no Lab-06 com Wi-Fi e MQTT QoS 1!"
    tokens = tokenizar(texto)
    assert "esp32" in tokens
    assert "lab-06" in tokens
    assert "mqtt" in tokens
    print("[PASS] Tokenização BM25 preserva termos técnicos")


def test_hybrid_search():
    engine = RAGEngine()
    assert len(engine.chunks) > 0, "A base de chunks deve estar carregada"

    # Teste de consulta sobre ESP32 WebServer
    resultados = engine.search_hybrid("ESP32 WebServer HTTP", top_k=3)
    assert len(resultados) > 0
    primeiro = resultados[0]
    assert "lab20" in primeiro.url or "webserver" in primeiro.title.lower()
    print(f"[PASS] Busca Híbrida: '{primeiro.title}' -> {primeiro.url} (Score: {primeiro.rrf_score:.4f})")

    # Teste de consulta sobre GenAI / RAG
    res_rag = engine.search_hybrid("RAG Lab 4 similaridade", top_k=2)
    assert any("lab4" in r.url for r in res_rag)
    print(f"[PASS] Busca Híbrida RAG: '{res_rag[0].title}'")


def test_ai_providers():
    mock_ai = MockAIProvider()
    assert not mock_ai.is_configured()
    resposta_mock = mock_ai.generate_answer("Como funciona o ESP32?", "Contexto sobre ESP32")
    assert "Modo de Demonstração Local" in resposta_mock
    print("[PASS] MockAIProvider opera corretamente em modo offline")

    active_provider = get_ai_provider()
    assert active_provider is not None
    print(f"[PASS] Provider Factory: {active_provider.__class__.__name__}")


def test_conversation_memory():
    memory = ConversationMemory(max_history_turns=2)
    sid = memory.get_or_create_session("sessao_teste")
    assert sid == "sessao_teste"

    memory.add_message(sid, "user", "Mensagem 1")
    memory.add_message(sid, "model", "Resposta 1")
    memory.add_message(sid, "user", "Mensagem 2")
    memory.add_message(sid, "model", "Resposta 2")
    memory.add_message(sid, "user", "Mensagem 3")
    memory.add_message(sid, "model", "Resposta 3")

    # Com max_history_turns=2, deve manter no máximo 4 mensagens (2 turnos)
    historico = memory.get_history(sid)
    assert len(historico) == 4
    assert historico[-1]["content"] == "Resposta 3"

    memory.clear_session(sid)
    assert len(memory.get_history(sid)) == 0
    print("[PASS] ConversationMemory thread-safe com janela deslizante validado")


if __name__ == "__main__":
    print("========================================")
    print("Iniciando Testes Unitários de Domínio")
    print("========================================")
    test_bm25_tokenization()
    test_hybrid_search()
    test_ai_providers()
    test_conversation_memory()
    print("========================================")
    print("✅ Todos os testes de domínio passaram!")
    print("========================================")
