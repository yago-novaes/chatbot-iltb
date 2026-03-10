from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_provider: str = "mock"
    llm_api_key: str = "mock"
    llm_model: str = "mock"
    llm_base_url: str = ""

    # RAG
    chroma_path: str = "./chroma_db"
    docs_path: str = "./docs"
    chunk_size: int = 800
    chunk_overlap: int = 100
    top_k_results: int = 4

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
