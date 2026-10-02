"""
Implementação dos Provedores de IA: GeminiProvider e MockAIProvider (SOLID - OCP, LSP)
"""

import os
from typing import List, Dict, Optional

from app.core.config import settings
from app.core.logging import logger
from app.services.base import BaseAIProvider

SYSTEM_PROMPT = """Você é o Assistente Virtual Oficial da disciplina "Disruptive Architectures: IA e IoT" (FIAP), ministrada pelo Prof. Arnaldo Viana.

Seu objetivo é sanar dúvidas de alunos sobre o conteúdo do curso com o mais alto nível de precisão técnica, clareza e fidelidade pedagógica.

REGRAS MANDATÓRIAS (GUARDRAILS):
1. **Fidelidade aos Documentos**: Responda baseando-se ESTRITAMENTE nas informações fornecidas no CONTEXTO DAS FONTES abaixo. Nunca invente ou alucine conteúdos não respaldados pelo material.
2. **Códigos e Sintaxe**: Quando o aluno perguntar sobre implementação de circuitos, Arduino, ESP32, Python, MQTT, Node-RED, Pydantic ou Colab, apresente o código limpo, comentado e dentro de blocos formatados (ex: ```cpp ou ```python).
3. **Guardrail de Escopo**: Se a pergunta não estiver presente no material fornecido ou for sobre temas alheios à disciplina, diga com transparência e educação:
   "Essa informação não consta no material oficial de Disruptive Architectures da disciplina. Posso te ajudar com os conteúdos de IoT (ESP32, Arduino, MQTT, Node-RED) ou GenAI (Prompts, Assistentes, Saídas Estruturadas e RAG)."
4. **Citações e Links**: Sempre conclua sua resposta indicando os links e seções oficiais das fontes consultadas para que o aluno possa aprofundar os estudos.
5. **Tom**: Didático, profissional, objetivo e encorajador.
"""


class GeminiProvider(BaseAIProvider):
    """Provedor concreto utilizando Google Gemini (Embeddings e LLM)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.client_genai = None
        self.legacy_genai = None
        self._initialize_sdk()

    def _initialize_sdk(self):
        if not self.api_key:
            logger.info("GeminiProvider: Nenhuma GEMINI_API_KEY configurada. Operando em modo de espera.")
            return

        # 1. Tenta novo SDK oficial google-genai (2.x)
        try:
            from google import genai
            self.client_genai = genai.Client(api_key=self.api_key)
            logger.info("GeminiProvider: Inicializado com google-genai 2.x com sucesso.")
            return
        except Exception as err:
            logger.debug(f"google-genai 2.x não inicializado: {err}")

        # 2. Fallback para google.generativeai
        try:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=self.api_key)
            self.legacy_genai = genai_legacy
            logger.info("GeminiProvider: Inicializado com google.generativeai legado com sucesso.")
        except Exception as err:
            logger.error(f"Falha ao inicializar SDKs do Gemini: {err}")

    def is_configured(self) -> bool:
        return bool(self.api_key and (self.client_genai or self.legacy_genai))

    def embed_query(self, query: str) -> Optional[List[float]]:
        if not self.is_configured():
            return None

        try:
            if self.client_genai:
                res = self.client_genai.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=query,
                )
                if res.embeddings:
                    return res.embeddings[0].values
            elif self.legacy_genai:
                res = self.legacy_genai.embed_content(
                    model=f"models/{settings.GEMINI_EMBEDDING_MODEL}",
                    content=query,
                    task_type="retrieval_query"
                )
                return res.get("embedding")
        except Exception as err:
            logger.warning(f"Erro ao gerar embedding com Gemini: {err}")
        return None

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

        try:
            if self.client_genai:
                from google.genai import types

                contents = []
                if conversation_history:
                    for turn in conversation_history[-4:]:
                        role = "user" if turn["role"] == "user" else "model"
                        contents.append(types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=turn["content"])]
                        ))

                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_prompt)]
                ))

                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.2,
                    max_output_tokens=1200,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                )

                response = self.client_genai.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=contents,
                    config=config,
                )
                return response.text or "Não foi possível gerar a resposta para esta pergunta."

            elif self.legacy_genai:
                model = self.legacy_genai.GenerativeModel(
                    model_name=settings.GEMINI_MODEL,
                    system_instruction=SYSTEM_PROMPT,
                    generation_config={"temperature": 0.2, "max_output_tokens": 1200}
                )
                response = model.generate_content(user_prompt)
                return response.text or "Não foi possível gerar a resposta para esta pergunta."

        except Exception as err:
            logger.error(f"Erro na geração com Gemini: {err}", exc_info=True)
            return f"Ocorreu uma instabilidade na consulta ao modelo: {str(err)}. Por favor, tente novamente em instantes."


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
