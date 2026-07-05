import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str

    # LLM APIs
    GEMINI_API_KEY: str
    GROQ_API_KEY: str

    # Search
    TAVILY_API_KEY: str

    # App config
    MAX_FILE_SIZE_MB: int = 20
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    ALLOWED_FILE_TYPES: list[str] = ["application/pdf",
                                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    # Placeholder user_id for single-user mode.
    # When Supabase Auth is added later, this will be replaced
    # by extracting user_id from the JWT token.
    DEFAULT_USER_ID: str = "00000000-0000-0000-0000-000000000001"

    model_config = {
        "env_file": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
