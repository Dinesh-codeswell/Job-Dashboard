"""
Configuration for Tech + Non-Tech Roles Dashboard.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
load_dotenv()


class Config:
    """Dashboard configuration."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5001))
    HOST = os.getenv('HOST', '0.0.0.0')

    # Notion
    NOTION_API_KEY = os.getenv('NOTION_API_KEY')
    NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')

    # Pagination
    JOBS_PER_PAGE = 30

    # Cache
    CACHE_TIMEOUT = 120  # seconds

    # Auto-refresh
    AUTO_REFRESH_INTERVAL = 60  # seconds (frontend polling)
