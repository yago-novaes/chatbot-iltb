"""
Cliente LLM unificado via interface OpenAI-compatible.
Suporta: Groq, OpenAI, Ollama, e modo mock (sem chave).
Histórico de conversa adicionado na Fase 2 (session manager).

Rate-limit handling:
  - 429 TPM (tokens per minute): retry com backoff exponencial (até 3x, espera 60s)
  - 429 TPD (tokens per day):    levanta TPDExhaustedError — sem retry possível
"""
import asyncio
import logging
from typing import List

from openai import AsyncOpenAI, RateLimitError

from app.src.config import settings
from app.src.llm.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

_TPM_WAIT_SECONDS = 65   # espera após erro TPM antes de retry
_MAX_TPM_RETRIES = 3


class TPDExhaustedError(RuntimeError):
    """Limite diário de tokens do Groq atingido. Não há como recuperar sem esperar ~24h."""


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

    Levanta TPDExhaustedError se o limite diário do Groq for atingido.
    Faz retry automático (até 3x) para erros de TPM (tokens por minuto).
    """
    if settings.llm_provider == "mock" or settings.llm_api_key in ("mock", "", None):
        return _mock_response(question, context)

    for attempt in range(1, _MAX_TPM_RETRIES + 2):  # +2: tentativa inicial + retries
        try:
            response = await _get_client().chat.completions.create(
                model=settings.llm_model,
                messages=_build_messages(context, question, history),
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
            )
            return response.choices[0].message.content.strip()

        except RateLimitError as e:
            err_str = str(e).lower()
            if "per day" in err_str or "tokens per day" in err_str or "tpd" in err_str.upper():
                raise TPDExhaustedError(
                    f"Limite diário de tokens Groq atingido. Aguarde ~24h.\nDetalhe: {e}"
                ) from e
            # TPM ou outro rate limit — retry com backoff
            if attempt <= _MAX_TPM_RETRIES:
                logger.warning(
                    "TPM rate limit (tentativa %d/%d). Aguardando %ds...",
                    attempt, _MAX_TPM_RETRIES, _TPM_WAIT_SECONDS,
                )
                await asyncio.sleep(_TPM_WAIT_SECONDS)
            else:
                raise

        except Exception as e:
            return (
                f"Erro ao chamar o LLM ({settings.llm_provider}): {e}\n\n"
                "Verifique LLM_API_KEY e LLM_BASE_URL no .env."
            )
