@echo off
echo ========================================
echo  🎯 RoleBoard - Tech & Non-Tech Jobs Dashboard
echo ========================================
echo.

:: Navigate to script directory
cd /d "%~dp0"

:: Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo.
    echo Creating .env from .env.example...
    echo Please edit .env with your Notion API key
    copy .env.example .env >nul
    echo.
    echo 📝 Edit marketing-dashboard\.env with your credentials
    echo    NOTION_API_KEY=your_key_here
    echo    NOTION_DATABASE_ID=your_database_id
    echo.
)

:: Activate virtual environment if exists
if exist "..\venv\Scripts\activate.bat" (
    call ..\venv\Scripts\activate.bat
)

:: Install dependencies if needed
echo 📦 Checking dependencies...
python -c "import flask; import notion_client" 2>nul || (
    echo Installing required packages...
    pip install flask flask-cors python-dotenv notion-client
)

echo.
echo 🚀 Starting RoleBoard Dashboard...
echo    Open: http://localhost:5001
echo.
python app.py

pause
