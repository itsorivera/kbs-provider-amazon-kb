from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AWS_REGION: str = "us-east-1"
    AWS_PROFILE: str | None = None
    KNOWLEDGE_BASE_TAG_KEY: str = "mcp-multirag-kb"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
