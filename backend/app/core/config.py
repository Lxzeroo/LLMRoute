from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LLMRoute"
    app_version: str = "0.1.0"

    ollama_base_url: str = "http://localhost:11434"

    small_model: str = "qwen2.5:1.5b"
    large_model: str = "qwen2.5:7b"
    embedding_model: str = "all-minilm:22m"

    cache_similarity_threshold: float = 0.90
    cache_ttl_seconds: int = 86400

    max_concurrent_requests: int = 1
    model_keep_alive: int = 0
    context_window: int = 2048
    max_output_tokens: int = 512
    temperature: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()