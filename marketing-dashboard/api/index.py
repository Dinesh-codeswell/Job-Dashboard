"""
RoleBoard - Vercel Serverless Entry Point
Serves the marketing dashboard Flask app as a Vercel serverless function.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path so app.py can find its imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the Flask app from the dashboard
# Vercel provides environment variables via the dashboard
from app import app


def handler(request):
    """Vercel serverless function handler."""
    return app(request.environ, lambda *args: None)
