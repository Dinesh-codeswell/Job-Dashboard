@echo off
REM LinkedIn Jobs Scraper to Notion - Quick Runner
REM Scrapes India core technical/business jobs from past 24 hours

echo ================================================================
echo LinkedIn Jobs Scraper - India to Notion
echo ================================================================
echo.

cd /d %~dp0

REM Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Please copy .env.example.notion to .env and add your Notion credentials.
    echo.
    copy .env.example.notion .env
    echo Created .env from template - please edit it with your credentials.
    pause
    exit /b 1
)

REM Check if LinkedIn session exists
if not exist linkedin_session.json (
    echo [WARNING] LinkedIn session not found!
    echo Creating new session...
    echo.
    python samples/create_session.py
    if errorlevel 1 (
        echo Failed to create LinkedIn session.
        pause
        exit /b 1
    )
)

REM Run the scraper
echo Starting job scraper...
echo.
python scrape_india_jobs_notion.py --limit 15

echo.
echo ================================================================
echo Done! Check your Notion database for new jobs.
echo ================================================================
pause
