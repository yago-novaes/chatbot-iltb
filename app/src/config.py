"""
Configuração da aplicação — produção.
Lê variáveis do .env via pydantic-settings.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # RAG
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    chroma_path: str = "./chroma_db"
    chroma_collection: str = "iltb_protocols"
    retriever_top_k: int = 4
    retriever_score_threshold: float = 0.50

    # Session
    session_max_messages: int = 10
    session_ttl_minutes: int = 30

    # API
    api_title: str = "Chatbot ILTB"
    api_version: str = "0.1.0"
    log_level: str = "INFO"

    # WhatsApp (Phase 2)
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
