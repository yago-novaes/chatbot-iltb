from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_provider: str = "mock"
    llm_api_key: str = "mock"
    llm_model: str = "mock"
    llm_base_url: str = ""
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024

    # RAG
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    chroma_path: str = "./chroma_db"
    chroma_collection: str = "iltb_protocols"
    docs_path: str = "./docs/protocolos"
    chunk_size: int = 800
    retriever_top_k: int = 4
    retriever_score_threshold: float = 0.40

    # Hybrid retrieval (TF2 — busca híbrida BM25+denso com RRF)
    retriever_mode: str = "dense"          # "dense" | "hybrid" | "hybrid_rerank"
    retriever_fetch_k: int = 20             # candidatos por ranker antes do RRF
    retriever_rrf_k: int = 60               # constante k do Reciprocal Rank Fusion

    # Reranker cross-encoder (TF1 — mGTE)
    reranker_model: str = "Alibaba-NLP/gte-multilingual-reranker-base"
    reranker_fetch_k: int = 20              # candidatos vindos do hybrid antes do rerank

    # Session (Phase 2)
    session_max_messages: int = 10
    session_ttl_minutes: int = 30

    # API
    api_title: str = "Chatbot ILTB"
    api_version: str = "0.2.0"
    log_level: str = "INFO"

    # WhatsApp (Phase 2)
    whatsapp_verify_token: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""

    # RAGAS evaluator — LLM juiz (pode ser diferente do LLM de produção)
    # Se vazio, usa o LLM de produção como fallback
    ragas_llm_provider: str = ""
    ragas_llm_api_key: str = ""
    ragas_llm_model: str = ""
    ragas_llm_base_url: str = ""


settings = Settings()
