import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "FactGuard AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    
    LLM_PROVIDER: str = "gemini" # gemini, openai, anthropic, mock
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    SEARCH_PROVIDER: str = "duckduckgo" # duckduckgo, tavily, serpapi
    TAVILY_API_KEY: str = ""
    SERPAPI_API_KEY: str = ""
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./factguard.db"
    CHROMA_DB_PATH: str = "./chroma_db"
    
    SECRET_KEY: str = "factguard_super_secret_key_2026"
    ALLOWED_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "*"
    ]
    
    DEMO_MODE: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
