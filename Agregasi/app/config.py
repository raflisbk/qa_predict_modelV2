from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APIFY_TOKEN: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    GLOBAL_RATE_LIMIT: int = 500

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
