"""
Testes de Integração da API FastAPI com TestClient e Lifespan
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["chunks_count"] > 0
    assert data["bm25_ready"] is True
    assert data["vectors_ready"] is True
    print(f"[PASS] /api/health: {data['chunks_count']} chunks ativos (BM25: True, Vetores: True).")


def test_api_search():
    response = client.get("/api/search?q=MQTT")
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    primeiro = data["results"][0]
    assert "mqtt" in primeiro["title"].lower() or "mqtt" in primeiro["content"].lower()
    print(f"[PASS] /api/search: {data['total_results']} chunks encontrados para 'MQTT'.")


def test_api_chat_flow():
    payload = {
        "message": "Como funciona o WebServer no ESP32?",
        "session_id": "integration_test_session"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["answer"]) > 0
    assert data["session_id"] == "integration_test_session"
    assert len(data["sources"]) > 0
    assert data["latency_ms"] >= 0
    print(f"[PASS] /api/chat: Resposta gerada em {data['latency_ms']}ms com {len(data['sources'])} fontes.")

    # Teste de listagem de sessões
    res_list = client.get("/api/chat/sessions")
    assert res_list.status_code == 200
    sessions_list = res_list.json()
    assert len(sessions_list) > 0
    assert any(s["id"] == payload["session_id"] for s in sessions_list)
    print(f"[PASS] GET /api/chat/sessions: {len(sessions_list)} sessões listadas na barra lateral.")

    # Teste de detalhes da sessão
    res_detail = client.get(f"/api/chat/session/{payload['session_id']}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert len(detail_data["messages"]) >= 2
    print(f"[PASS] GET /api/chat/session/{payload['session_id']}: {len(detail_data['messages'])} mensagens recuperadas.")

    # Teste de renomear título da conversa
    res_patch = client.patch(
        f"/api/chat/session/{payload['session_id']}/title",
        json={"title": "Aula de ESP32 WebServer"}
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["title"] == "Aula de ESP32 WebServer"
    print("[PASS] PATCH /api/chat/session/title: Título atualizado com sucesso.")

    # Teste de exclusão de sessão
    res_del = client.delete(f"/api/chat/session/{payload['session_id']}")
    assert res_del.status_code == 200
    assert res_del.json()["cleared"] is True
    print(f"[PASS] DELETE /api/chat/session: Sessão limpa com sucesso.")


def test_static_ui_endpoints():
    res_ui = client.get("/chat")
    assert res_ui.status_code == 200
    assert "Assistente RAG" in res_ui.text
    print(f"[PASS] /chat: Interface Web renderizada com sucesso ({len(res_ui.text)} bytes).")

    res_widget = client.get("/widget.js")
    assert res_widget.status_code == 200
    assert "da-widget-root" in res_widget.text
    print(f"[PASS] /widget.js: Script servido com sucesso ({len(res_widget.text)} bytes).")


if __name__ == "__main__":
    print("========================================")
    print("Iniciando Testes de Integração da API")
    print("========================================")
    test_api_health()
    test_api_search()
    test_api_chat_flow()
    test_static_ui_endpoints()
    print("========================================")
    print("✅ Todos os testes da API foram aprovados!")
    print("========================================")
