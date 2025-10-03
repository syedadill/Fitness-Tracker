"""Configuration management for Fitness Tracker application."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # MongoDB settings
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "fitness_tracker")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Cache settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        return bool(cls.MONGO_URI and cls.MONGO_DB_NAME and cls.REDIS_URL)


config = Config()
