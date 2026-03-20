"""
Cliente LLM unificado via interface OpenAI-compatible.
Suporta: Groq, OpenAI, Ollama, e modo mock (sem chave).
Histórico de conversa adicionado na Fase 2 (session manager).
"""
from typing import List

from openai import AsyncOpenAI

from app.src.config import settings
from app.src.llm.prompts import SYSTEM_PROMPT

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url or None,
        )
    return _client


def _build_messages(context: str, question: str, history: List[dict] | None = None) -> List[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"## Contexto dos Protocolos ILTB\n\n{context}\n\n## Pergunta\n\n{question}",
    })
    return messages


def _mock_response(question: str, context: str) -> str:
    return (
        "[MODO MOCK — sem chave de API configurada]\n\n"
        f"Pergunta: '{question}'\n\n"
        f"Contexto recuperado ({len(context)} chars): {context[:400]}...\n\n"
        "Configure LLM_API_KEY no .env. Opção gratuita: Groq (https://console.groq.com)"
    )


async def generate(context: str, question: str, history: List[dict] | None = None) -> str:
    """
    Gera resposta via LLM configurado (async).
    history: lista de mensagens anteriores [{role, content}] para contexto de sessão.
    """
    if settings.llm_provider == "mock" or settings.llm_api_key in ("mock", "", None):
        return _mock_response(question, context)

    try:
        response = await _get_client().chat.completions.create(
            model=settings.llm_model,
            messages=_build_messages(context, question, history),
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return (
            f"Erro ao chamar o LLM ({settings.llm_provider}): {e}\n\n"
            "Verifique LLM_API_KEY e LLM_BASE_URL no .env."
        )
