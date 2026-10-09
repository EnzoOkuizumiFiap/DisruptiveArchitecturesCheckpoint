"""
Implementação dos Provedores de IA: GeminiProvider e MockAIProvider (SOLID - OCP, LSP)
"""

import os
import re
import time
import threading
from typing import List, Dict, Optional, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.services.base import BaseAIProvider

SYSTEM_PROMPT = """Você é o Assistente Virtual Oficial da disciplina "Disruptive Architectures: IA e IoT" (FIAP), ministrada pelo Prof. Arnaldo Viana.

Seu objetivo é sanar dúvidas de alunos sobre o conteúdo do curso com o mais alto nível de precisão técnica, clareza e fidelidade pedagógica.

REGRAS MANDATÓRIAS (GUARDRAILS E DIRETRIZES):
1. **Fidelidade aos Documentos e Escopo da Disciplina**:
   - Responda baseando-se nas informações e códigos fornecidos no CONTEXTO DAS FONTES abaixo e na ementa oficial.
   - Os domínios centrais da disciplina compreendem:
     * **IoT e Sistemas Embarcados**: Arduino, ESP32 (GPIOs, pinos, WebServer, Wi-Fi, APIs REST, MQTT, Node-RED e C++).
     * **GenAI e RAG**: Engenharia de Prompts (Lab 1), Assistentes (Lab 2), Ferramentas e Pydantic (Lab 3), e **RAG e Bases de Conhecimento (Lab 4 / CP5)**, incluindo embeddings, similaridade de cosseno, busca densa, busca esparsa (BM25 Okapi), fusão por Reciprocal Rank Fusion (RRF) e mitigação de alucinações.
   - Sempre que o aluno perguntar sobre esses temas ou sobre como funciona o pipeline de RAG híbrido, responda com riqueza técnica, didática e clareza conceitual.

2. **Tratamento de Escopo e Recursos Não Ministrados (Guardrail Adaptativo)**:
   - **Temas 100% alheios à disciplina** (ex: esportes, culinária, finanças pessoais, notícias gerais ou assuntos sem relação com IoT/GenAI): Diga com transparência e educação:
     "Essa informação não consta no material oficial de Disruptive Architectures da disciplina. Posso te ajudar com os conteúdos de IoT (ESP32, Arduino, MQTT, Node-RED) ou GenAI (Prompts, Assistentes, Saídas Estruturadas e RAG)."
   - **Solicitações técnicas de IoT com bibliotecas complexas não ensinadas** (ex: FreeRTOS em vez de loop/millis, bibliotecas assíncronas externas de terceiros):
     Pontue brevemente com clareza pedagógica que tais recursos avançados não fazem parte do escopo dos laboratórios básicos da disciplina. Em seguida, FORNEÇA a solução adaptada utilizando as práticas, bibliotecas e funções oficiais ensinadas nos laboratórios do curso (ex: WebServer padrão do ESP32, millis(), analogRead, PubSubClient para MQTT, etc.).

3. **Códigos e Sintaxe**:
   - Quando o aluno perguntar sobre implementação técnica (Arduino, ESP32, Python, MQTT, Node-RED, Pydantic, etc.), apresente o código limpo, comentado, pronto para compilar e dentro de blocos formatados (ex: ```cpp ou ```python).

4. **Citações e Links**:
   - Sempre conclua sua resposta indicando os links e seções oficiais das fontes consultadas para que o aluno possa aprofundar os estudos.

5. **Tom**:
   - Didático, profissional, objetivo, encorajador e focado no aprendizado prático da ementa oficial.

6. **Formatação e Legibilidade Visual (Markdown Rigoroso)**:
   - Insira OBRIGATORIAMENTE duas quebras de linha (`\\n\\n`) antes e depois de qualquer título Markdown (ex: `\\n\\n### Título\\n\\n`). NUNCA cole títulos no final ou início de frases.
   - Separe CADA item de listas numeradas ou com marcadores em uma linha própria com quebra de linha (ex: `\\n1. Item 1\\n2. Item 2`).
   - Separe cada parágrafo com uma linha em branco (`\\n\\n`). NUNCA junte frases ou seções em um bloco de texto contínuo sem quebras.
   - Use **negrito** nos conceitos principais para facilitar a leitura rápida do aluno.
"""


def sanitize_markdown_output(text: str) -> str:
    """
    Higieniza a formatação Markdown da resposta gerada:
    Garante quebras de linha adequadas para títulos, listas e parágrafos mesmo se o LLM aglutinar o texto.
    """
    if not text:
        return text

    # Corrige títulos colados em texto anterior (ex: "disciplina.### O que é" -> "disciplina.\n\n### O que é")
    cleaned = re.sub(r"([^\n])\s*(#{1,6}\s+)", r"\1\n\n\2", text)

    # Corrige início de parágrafo colado imediatamente após um título com '?' ou ':' (ex: "Arduino?A linguagem" -> "Arduino?\n\nA linguagem")
    cleaned = re.sub(r"(#{1,6}\s+[^\n]+?[?!:])([A-ZÀ-Ú])", r"\1\n\n\2", cleaned)

    # Corrige listas numeradas coladas em dois-pontos ou pontos (ex: ":1. Sintaxe" -> ":\n\n1. Sintaxe", ".2. Funções" -> ".\n\n2. Funções")
    cleaned = re.sub(r":\s*(\d+\.\s+)", r":\n\n\1", cleaned)
    cleaned = re.sub(r"([.!?])\s*(\d+\.\s+)", r"\1\n\n\2", cleaned)

    # Corrige frases coladas após ponto final sem espaço (ex: "microcontroladores.O aprendizado" -> "microcontroladores.\n\nO aprendizado")
    cleaned = re.sub(r"([.!?])([A-ZÀ-Ú])", r"\1\n\n\2", cleaned)

    # Normaliza quebras excessivas
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


class GeminiProvider(BaseAIProvider):
    """
    Provedor de IA utilizando EXCLUSIVAMENTE o novo SDK oficial do Google GenAI (google-genai).
    Implementa as melhores práticas de Clean Code, cache em memória e alta resiliência.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.client = None
        # Cache em memória thread-safe para embeddings de consultas frequentes
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_lock = threading.Lock()
        self._max_cache_size: int = 500
        self._initialize_sdk()

    def _initialize_sdk(self):
        if not self.api_key:
            logger.info("GeminiProvider: Nenhuma GEMINI_API_KEY configurada. Operando em modo de espera.")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"GeminiProvider: Conectado com sucesso ao SDK Oficial Google GenAI ({settings.GEMINI_MODEL}).")
        except Exception as err:
            logger.error(f"Falha ao inicializar o SDK Google GenAI: {err}", exc_info=True)
            self.client = None

    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)

    def embed_query(self, query: str) -> Optional[List[float]]:
        if not self.is_configured():
            return None

        clean_query = query.strip().lower()
        if not clean_query:
            return None

        # 1. Verifica cache em memória (0ms latency)
        with self._cache_lock:
            if clean_query in self._embedding_cache:
                return self._embedding_cache[clean_query]

        # 2. Gera novo embedding via API oficial Google GenAI com retry
        for attempt in range(1, 3):
            try:
                res = self.client.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=query,
                )
                if res.embeddings:
                    embedding = res.embeddings[0].values
                    with self._cache_lock:
                        if len(self._embedding_cache) >= self._max_cache_size:
                            # Remove o item mais antigo (FIFO/LRU simples)
                            self._embedding_cache.pop(next(iter(self._embedding_cache)))
                        self._embedding_cache[clean_query] = embedding
                    return embedding

            except Exception as err:
                logger.warning(f"Tentativa {attempt} de embedding com Google GenAI falhou: {err}")
                if attempt == 1:
                    time.sleep(0.5)

        return None

    def _sanitize_turns(self, history: Optional[List[Dict[str, str]]]) -> List[Tuple[str, str]]:
        """
        Valida e assegura alternância estrita entre 'user' e 'model' para o Gemini.
        Remove turnos consecutivos do mesmo papel e garante término pronto para nova pergunta.
        """
        if not history:
            return []

        sanitized: List[Tuple[str, str]] = []
        last_role = None

        for turn in history[-6:]:
            role = "user" if turn.get("role") == "user" else "model"
            content = turn.get("content", "").strip()
            if not content:
                continue
            if role != last_role:
                sanitized.append((role, content))
                last_role = role

        # Se o último turno do histórico foi 'user', descarta para que a nova pergunta seja 'user'
        if sanitized and sanitized[-1][0] == "user":
            sanitized.pop()

        return sanitized

    def generate_answer(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        if not self.is_configured():
            return MockAIProvider().generate_answer(question, context, conversation_history)

        user_prompt = (
            f"CONTEXTO DAS FONTES (MATERIAL OFICIAL DA DISCIPLINA):\n"
            f"{context}\n\n"
            f"PERGUNTA DO ALUNO:\n{question}\n\n"
            f"Responda fundamentando-se nas fontes acima com precisão e clareza didática."
        )

        sanitized_history = self._sanitize_turns(conversation_history)

        # Loop de resiliência com backoff exponencial (até 2 retries)
        last_error = None
        for attempt in range(1, 3):
            try:
                from google.genai import types

                contents = []
                for role, text in sanitized_history:
                    contents.append(types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=text)]
                    ))

                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_prompt)]
                ))

                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=2048,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                )

                response = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=contents,
                    config=config,
                )
                raw_text = response.text or "Não foi possível gerar a resposta para esta pergunta."
                return sanitize_markdown_output(raw_text)

            except Exception as err:
                last_error = err
                logger.warning(f"Tentativa {attempt} com Google GenAI falhou ({err}). Realizando retry...")
                if attempt == 1:
                    time.sleep(1.0)

        logger.error(f"Todas as tentativas com Google GenAI falharam: {last_error}", exc_info=True)
        return f"Ocorreu uma instabilidade na consulta ao modelo: {str(last_error)}. Por favor, tente novamente em instantes."


class MockAIProvider(BaseAIProvider):
    """Provedor Mock para testes e execução local sem API Key."""

    def is_configured(self) -> bool:
        return False

    def embed_query(self, query: str) -> Optional[List[float]]:
        return None

    def generate_answer(
        self,
        question: str,
        context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        trecho_preview = context[:750].strip() if context else "Nenhum contexto recuperado."
        return (
            "⚠️ **Modo de Demonstração Local (Sem API Key)**\n\n"
            "A chave `GEMINI_API_KEY` ainda não foi configurada no arquivo `.env` ou variáveis de ambiente.\n\n"
            "**Trechos recuperados da documentação oficial:**\n\n"
            f"{trecho_preview}...\n\n"
            "*(Para ativar respostas completas geradas pelo Gemini 1.5/2.5 Flash, insira sua chave `GEMINI_API_KEY` no `.env`)*"
        )


def get_ai_provider() -> BaseAIProvider:
    """Factory function para obter o provedor de IA ativo."""
    provider = GeminiProvider()
    if provider.is_configured():
        return provider
    return MockAIProvider()
