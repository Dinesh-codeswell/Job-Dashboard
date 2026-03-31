"""
Configuration for Consulting Jobs Dashboard
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Also try current directory
load_dotenv()

class Config:
    """Dashboard configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # Google Sheets - Look for credentials in parent directory first
    GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
    
    # Check multiple locations for credentials file
    for creds_path in [
        os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json'),
        Path(__file__).parent.parent / 'credentials.json',
        Path(__file__).parent / 'credentials.json',
        'credentials.json'
    ]:
        if Path(creds_path).exists():
            GOOGLE_CREDENTIALS_FILE = str(creds_path)
            break
    else:
        GOOGLE_CREDENTIALS_FILE = 'credentials.json'
    
    WORKSHEET_NAME = os.getenv('WORKSHEET_NAME', 'Consulting_Jobs_India')
    
    # Pagination
    JOBS_PER_PAGE = 30
    
    # Cache
    CACHE_TIMEOUT = 60  # seconds
    
    # Auto-refresh
    AUTO_REFRESH_INTERVAL = 60  # seconds (frontend polling)
