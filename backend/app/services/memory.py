"""
Gerenciador de Memória Conversacional Multi-turn com Persistência
Thread-safe, com persistência em disco (sessions.json) e navegação entre conversas.
"""

import json
import time
import uuid
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any

from app.core.config import settings
from app.core.logging import logger
from app.services.base import BaseSessionManager

SESSIONS_FILE = settings.BASE_DIR / "data" / "sessions.json"


class ConversationMemory(BaseSessionManager):
    """Gerenciador de sessões persistente com suporte a histórico completo e títulos."""

    def __init__(
        self,
        max_history_turns: int = 10,
        ttl_seconds: int = 3600 * 24 * 7,  # 7 dias de persistência
        storage_path: Optional[Path] = None
    ):
        self.max_history_turns = max_history_turns
        self.ttl_seconds = ttl_seconds
        self.storage_path = storage_path or SESSIONS_FILE
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._load_from_disk()

    def _load_from_disk(self):
        """Carrega sessões salvas em disco se existirem e purga expiradas."""
        if self.storage_path and self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8-sig"))
                self.sessions = data
                self._prune_expired_sessions(time.time())
                logger.info(f"ConversationMemory: {len(self.sessions)} sessões ativas carregadas de {self.storage_path.name}")
            except Exception as err:
                logger.error(f"Erro ao carregar sessões de {self.storage_path}: {err}")
                self.sessions = {}

    def _prune_expired_sessions(self, now: float):
        """Remove sessões inativas que excederam o tempo limite (TTL)."""
        cutoff = now - self.ttl_seconds
        expired_keys = [
            sid for sid, s in self.sessions.items()
            if s.get("last_active", s.get("created_at", 0)) < cutoff
        ]
        for sid in expired_keys:
            del self.sessions[sid]

    def _save_to_disk(self):
        """
        Salva o estado atual das sessões em disco de forma estritamente ATÔMICA.
        Escreve em arquivo temporário e faz o replace para impedir qualquer risco de corrupção.
        """
        if not self.storage_path:
            return
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._prune_expired_sessions(time.time())
            temp_path = self.storage_path.with_suffix(f".tmp_{uuid.uuid4().hex[:6]}")
            content = json.dumps(self.sessions, ensure_ascii=False, indent=2)
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(self.storage_path)
        except Exception as err:
            logger.error(f"Erro ao salvar sessões atômicas em disco: {err}")

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        with self._lock:
            now = time.time()
            if not session_id or session_id.strip() == "":
                session_id = str(uuid.uuid4())

            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "id": session_id,
                    "title": "Nova Conversa",
                    "created_at": now,
                    "last_active": now,
                    "messages": []
                }
                logger.debug(f"Nova sessão de chat criada: {session_id}")
                self._save_to_disk()
            else:
                self.sessions[session_id]["last_active"] = now

            return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        latency_ms: Optional[float] = None
    ) -> None:
        with self._lock:
            now = time.time()
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    "id": session_id,
                    "title": "Nova Conversa",
                    "created_at": now,
                    "last_active": now,
                    "messages": []
                }

            session = self.sessions[session_id]
            session["last_active"] = now

            # Auto-título com base na primeira mensagem do usuário
            if role == "user" and session.get("title") in ("Nova Conversa", "", None):
                titulo_limpo = content.strip().replace("\n", " ")
                if len(titulo_limpo) > 38:
                    titulo_limpo = titulo_limpo[:35].rstrip() + "..."
                session["title"] = titulo_limpo

            msg_entry = {
                "role": role,
                "content": content,
                "timestamp": now,
                "sources": sources or [],
                "latency_ms": latency_ms
            }
            session["messages"].append(msg_entry)

            # Mantém os últimos turnos no histórico
            max_msgs = self.max_history_turns * 2
            if len(session["messages"]) > max_msgs:
                session["messages"] = session["messages"][-max_msgs:]

            self._save_to_disk()

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]["last_active"] = time.time()
                return [
                    {"role": m["role"], "content": m["content"]}
                    for m in self.sessions[session_id]["messages"]
                ]
            return []

    def get_session_detail(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retorna detalhes completos e mensagens de uma sessão."""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]["last_active"] = time.time()
                return dict(self.sessions[session_id])
            return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Retorna sumário de todas as sessões ordenadas pela mais recente."""
        with self._lock:
            resumo = []
            for sid, s in self.sessions.items():
                resumo.append({
                    "id": sid,
                    "title": s.get("title", "Conversa"),
                    "created_at": s.get("created_at", 0),
                    "last_active": s.get("last_active", 0),
                    "message_count": len(s.get("messages", []))
                })
            # Ordena por atividade mais recente
            resumo.sort(key=lambda x: x["last_active"], reverse=True)
            return resumo

    def update_title(self, session_id: str, new_title: str) -> bool:
        """Permite ao usuário renomear uma conversa na barra lateral."""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]["title"] = new_title.strip()
                self._save_to_disk()
                return True
            return False

    def clear_session(self, session_id: str) -> bool:
        """Exclui a sessão da memória e do disco."""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                self._save_to_disk()
                logger.info(f"Sessão {session_id} removida.")
                return True
            return False


# Instância global singleton
memory_manager = ConversationMemory()
