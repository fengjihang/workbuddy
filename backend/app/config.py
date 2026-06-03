from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    embedding_model: str = "text-embedding-3-small"

    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./zcm.db"

    upload_dir: str = "uploads"
    export_dir: str = "exports"
    chroma_dir: str = "chroma_data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
