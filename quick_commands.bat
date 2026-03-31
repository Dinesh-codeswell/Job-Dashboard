@echo off
REM ================================================================================
REM                    LINKEDIN JOB SCRAPER - QUICK COMMANDS
REM                         Windows Batch Shortcuts
REM ================================================================================

echo.
echo ================================================================================
echo                    LINKEDIN JOB SCRAPER - QUICK COMMANDS
echo ================================================================================
echo.

:MENU
echo Select an option:
echo.
echo 1. Scrape Data Analyst - Remote (15 jobs)
echo 2. Scrape Data Analyst - India (15 jobs)
echo 3. Scrape Data Analyst - US (15 jobs)
echo 4. Scrape Business Analyst - Remote (15 jobs)
echo 5. Scrape Software Engineer - Remote (15 jobs)
echo 6. Scrape Internships - Remote (15 jobs)
echo 7. Scrape Entry Level - Remote (15 jobs)
echo 8. Scrape Senior Level - Remote (15 jobs)
echo 9. Custom Search
echo.
echo 10. Check Total Jobs in Sheet
echo 11. Export Jobs to CSV
echo 12. Create New LinkedIn Session
echo.
echo 13. Help (Show all commands)
echo 0. Exit
echo.
echo ================================================================================
echo.

set /p choice="Enter your choice (0-13): "

if "%choice%"=="1" goto scrape_da_remote
if "%choice%"=="2" goto scrape_da_india
if "%choice%"=="3" goto scrape_da_us
if "%choice%"=="4" goto scrape_ba_remote
if "%choice%"=="5" goto scrape_swe_remote
if "%choice%"=="6" goto scrape_internship
if "%choice%"=="7" goto scrape_entry
if "%choice%"=="8" goto scrape_senior
if "%choice%"=="9" goto custom_search
if "%choice%"=="10" goto check_jobs
if "%choice%"=="11" goto export_csv
if "%choice%"=="12" goto create_session
if "%choice%"=="13" goto show_help
if "%choice%"=="0" goto exit

echo Invalid choice! Please try again.
goto MENU

:scrape_da_remote
echo.
echo Scraping Data Analyst - Remote jobs...
python jobs_to_sheets.py -k "Data Analyst" -l "Remote" --limit 15
goto end

:scrape_da_india
echo.
echo Scraping Data Analyst - India jobs...
python jobs_to_sheets.py -k "Data Analyst" -l "India" --limit 15
goto end

:scrape_da_us
echo.
echo Scraping Data Analyst - United States jobs...
python jobs_to_sheets.py -k "Data Analyst" -l "United States" --limit 15
goto end

:scrape_ba_remote
echo.
echo Scraping Business Analyst - Remote jobs...
python jobs_to_sheets.py -k "Business Analyst" -l "Remote" --limit 15
goto end

:scrape_swe_remote
echo.
echo Scraping Software Engineer - Remote jobs...
python jobs_to_sheets.py -k "Software Engineer" -l "Remote" --limit 15
goto end

:scrape_internship
echo.
echo Scraping Internship - Remote jobs...
python jobs_to_sheets.py -k "Data Analyst internship" -l "Remote" --limit 15
goto end

:scrape_entry
echo.
echo Scraping Entry Level - Remote jobs...
python jobs_to_sheets.py -k "Entry level Data Analyst" -l "Remote" --limit 15
goto end

:scrape_senior
echo.
echo Scraping Senior Level - Remote jobs...
python jobs_to_sheets.py -k "Senior Data Analyst" -l "Remote" --limit 15
goto end

:custom_search
echo.
set /p keyword="Enter job keyword: "
set /p location="Enter location (or press Enter for Remote): "
if "%location%"=="" set location=Remote
set /p limit="Enter number of jobs (default 15): "
if "%limit%"=="" set limit=15
python jobs_to_sheets.py -k "%keyword%" -l "%location%" --limit %limit%
goto end

:check_jobs
echo.
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Jobs_v2'); print(f'Total jobs in sheet: {len(gs.get_all_jobs())}')"
goto end

:export_csv
echo.
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; import csv; gs = GoogleSheetsIntegration(); gs.connect('Jobs_v2'); jobs = gs.get_all_jobs(); f=open('jobs_export.csv','w',newline='',encoding='utf-8'); w=csv.DictWriter(f,fieldnames=jobs[0].keys()); w.writeheader(); w.writerows(jobs); f.close(); print('Exported to jobs_export.csv')"
goto end

:create_session
echo.
echo Creating new LinkedIn session...
python samples\create_session.py
goto end

:show_help
echo.
type COMMANDS_REFERENCE.txt
goto end

:exit
echo.
echo Goodbye!
echo.
exit /b

:end
echo.
echo ================================================================================
echo.
set /p again="Do you want to perform another action? (Y/N): "
if /i "%again%"=="Y" goto MENU
echo.
echo Goodbye!
echo.
