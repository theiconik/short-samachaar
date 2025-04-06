from pydantic_settings import BaseSettings
from pydantic import field_validator
import os

class Settings(BaseSettings):
    # API Keys
    NEWS_API_KEY: str

    # Base URLs
    NEWS_API_BASE_URL: str = "https://newsdata.io/api/1/latest?apikey={}&country=in"

    # Formatted URLs (will be created using validators)
    NEWS_API_URL: str = ""

    # Elasticsearch Configuration
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Article Retention (days)
    ARTICLE_RETENTION_DAYS: int = 7

    # API Headers
    NEWS_API_HEADERS: dict = {}

    @field_validator('NEWS_API_URL')
    def format_news_api_url(cls, v, info):
        """Format the NEWS_API_URL with the API key"""
        return info.data['NEWS_API_BASE_URL'].format(info.data['NEWS_API_KEY'])

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()