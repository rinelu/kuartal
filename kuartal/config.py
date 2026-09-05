"""
All modules access environment variables and configuration through this module
to keep configuration handling consistent across the pipeline.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Sectors API
    sectors_api_key:  str = ""
    sectors_base_url: str = "https://api.sectors.app"

    # LLM
    llm_provider: str = "gemini" # gemini | openrouter | openai
    llm_api_key:  str = ""
    llm_model:    str = "gemini-1.5-flash"

    telegram_bot_token: str = ""
    telegram_chat_id:   str = ""

    kuartal_db_path: str = "./kuartal.db"

    api_host:  str  = "0.0.0.0"
    api_port:  int  = 8000
    mock_mode: bool = True

    poll_interval_seconds: int = 3600

    # Fallback LLM provider
    llm_fallback_provider: str = "openrouter"  # openrouter | groq | none
    llm_fallback_api_key:  str = ""
    llm_fallback_model:    str = "meta-llama/llama-3.1-8b-instruct"

    # Per-stage enable/disable
    pipeline_enable_llm:      bool = True
    pipeline_enable_delivery: bool = True

    # Basic scheduler process supervision.
    scheduler_restart_backoff_seconds: int = 5

settings = Settings()
