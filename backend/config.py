from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    FRONTEND_ORIGINS: str = 'http://localhost:5173'
    RESOURCE_DIR: str = 'rag/knowledge_base/raw'
    MAX_RESOURCE_MB: int = 20
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

settings = Settings()

def allowed_origins() -> list[str]:
    return [x.strip() for x in settings.FRONTEND_ORIGINS.split(',') if x.strip()]
