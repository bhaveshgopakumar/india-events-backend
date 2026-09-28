from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:rootpass@db:3306/india_events"
    secret_key: str = "change-me"
    access_token_minutes: int = 60 * 24
    cors_origins: str = "*"

settings = Settings()
