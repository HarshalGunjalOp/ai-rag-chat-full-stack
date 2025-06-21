from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 20
    CACHE_TTL: int = 3600  # 1hr

    # Redis
    REDIS_URL: str

    # OpenAI
    OPENAI_API_KEY: str

    # Tell pydantic where to find the .env file
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

