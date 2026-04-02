@echo off
REM Quick fix to run notion optimized scraper
REM This sets up the Python path correctly

cd /d %~dp0

REM Set PYTHONPATH to include current directory
set PYTHONPATH=%CD%

REM Run the scraper
C:\Users\katal\AppData\Local\Programs\Python\Python311\python.exe scrape_india_jobs_notion_optimized.py %*

pause
