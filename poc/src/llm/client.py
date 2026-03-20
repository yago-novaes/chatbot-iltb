"""
Cliente LLM unificado via interface OpenAI-compatible.
Suporta: Groq, OpenAI, Ollama, e modo mock (sem chave).
"""
from typing import List

from src.config import settings

SYSTEM_PROMPT = """Você é um assistente clínico especializado em ILTB (Infecção Latente pelo Mycobacterium tuberculosis), desenvolvido para apoiar enfermeiros da atenção primária e secundária.

Suas respostas devem:
- Ser baseadas EXCLUSIVAMENTE no contexto fornecido (protocolos do Ministério da Saúde)
- Ser objetivas, claras e em linguagem acessível para profissionais de saúde
- Indicar a fonte do trecho quando relevante
- Alertar quando a pergunta estiver fora do escopo dos protocolos disponíveis
- NUNCA inventar informações não presentes no contexto

Se o contexto não contiver informação suficiente para responder, diga: "Não encontrei essa informação nos protocolos disponíveis. Consulte o Manual de Recomendações do MS."
"""


def _build_prompt(context: str, question: str) -> List[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"## Contexto dos Protocolos ILTB\n\n{context}\n\n"
                f"## Pergunta\n\n{question}"
            ),
        },
    ]


def _mock_response(question: str, context: str) -> str:
    """Resposta simulada para rodar sem chave de API."""
    return (
        "[MODO MOCK — sem chave de API configurada]\n\n"
        f"Pergunta recebida: '{question}'\n\n"
        f"Contexto recuperado ({len(context)} caracteres):\n"
        f"{context[:400]}...\n\n"
        "Para respostas reais, configure LLM_API_KEY no arquivo .env.\n"
        "Opção gratuita: Groq em https://console.groq.com"
    )


def generate(context: str, question: str) -> str:
    """
    Gera uma resposta usando o LLM configurado.
    Fallback automático para mock se provider='mock' ou sem chave.
    """
    if settings.llm_provider == "mock" or settings.llm_api_key in ("mock", "", None):
        return _mock_response(question, context)

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url or None,
        )

        messages = _build_prompt(context, question)

        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.1,      # baixo para respostas mais factuais
            max_tokens=1024,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return (
            f"Erro ao chamar o LLM ({settings.llm_provider}): {e}\n\n"
            "Verifique LLM_API_KEY e LLM_BASE_URL no seu .env."
        )
