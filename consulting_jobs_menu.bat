@echo off
REM ================================================================================
REM                    CONSULTING JOBS SCRAPER - INDIA
REM                         Quick Commands Menu
REM ================================================================================

echo.
echo ================================================================================
echo                    CONSULTING JOBS SCRAPER - INDIA
echo                      Exclusively for Consulting Roles
echo ================================================================================
echo.

:MENU
echo Select an option:
echo.
echo === QUICK SCRAPES ===
echo 1. All Cities - Default (10 jobs per city)
echo 2. Tier 1 Cities Only - Metros (20 jobs per city)
echo 3. Bangalore - IT Capital (20 jobs)
echo 4. Mumbai - Financial Hub (20 jobs)
echo 5. Chennai - Consulting Hub (20 jobs)
echo 6. Pune - IT/Consulting (20 jobs)
echo 7. Hyderabad - Tech Hub (20 jobs)
echo 8. Gurugram/NCR - Corporate Hub (20 jobs)
echo.
echo === SPECIALIZED SEARCHES ===
echo 9. South India IT Corridor (Bangalore, Chennai, Hyderabad, Pune)
echo 10. Delhi NCR Region (Gurugram, Noida, Delhi)
echo 11. West India (Mumbai, Pune, Ahmedabad)
echo 12. High Volume Scan (25 jobs per city, Tier 1 only)
echo.
echo === OPTIONS ===
echo 13. Custom City Search
echo 14. Show Browser (Not Headless)
echo 15. Without Duplicate Check
echo.
echo === GOOGLE SHEETS ===
echo 16. Check Total Jobs
echo 17. View Jobs by City
echo 18. Export to CSV
echo 19. Find Big 4 Jobs (Deloitte, PwC, EY, KPMG)
echo 20. Find Jobs Posted Today
echo.
echo === MAINTENANCE ===
echo 21. Create New LinkedIn Session
echo 22. Show Help
echo.
echo 0. Exit
echo.
echo ================================================================================
echo.

set /p choice="Enter your choice (0-22): "

if "%choice%"=="1" goto scrape_all
if "%choice%"=="2" goto scrape_tier1
if "%choice%"=="3" goto scrape_bangalore
if "%choice%"=="4" goto scrape_mumbai
if "%choice%"=="5" goto scrape_chennai
if "%choice%"=="6" goto scrape_pune
if "%choice%"=="7" goto scrape_hyderabad
if "%choice%"=="8" goto scrape_gurugram
if "%choice%"=="9" goto scrape_south
if "%choice%"=="10" goto scrape_ncr
if "%choice%"=="11" goto scrape_west
if "%choice%"=="12" goto scrape_high_volume
if "%choice%"=="13" goto custom_search
if "%choice%"=="14" goto headless_off
if "%choice%"=="15" goto no_dedup
if "%choice%"=="16" goto check_jobs
if "%choice%"=="17" goto view_by_city
if "%choice%"=="18" goto export_csv
if "%choice%"=="19" goto find_big4
if "%choice%"=="20" goto find_today
if "%choice%"=="21" goto create_session
if "%choice%"=="22" goto show_help
if "%choice%"=="0" goto exit

echo Invalid choice! Please try again.
goto MENU

:scrape_all
echo.
echo Scraping consulting jobs from all Indian cities...
python scrape_consulting_india.py --limit-per-city 10
goto end

:scrape_tier1
echo.
echo Scraping Tier 1 cities (metros only)...
python scrape_consulting_india.py --tier-1-only --limit-per-city 20
goto end

:scrape_bangalore
echo.
echo Scraping Bangalore consulting jobs...
python scrape_consulting_india.py --cities "Bangalore" --limit-per-city 20
goto end

:scrape_mumbai
echo.
echo Scraping Mumbai consulting jobs...
python scrape_consulting_india.py --cities "Mumbai" --limit-per-city 20
goto end

:scrape_chennai
echo.
echo Scraping Chennai consulting jobs...
python scrape_consulting_india.py --cities "Chennai" --limit-per-city 20
goto end

:scrape_pune
echo.
echo Scraping Pune consulting jobs...
python scrape_consulting_india.py --cities "Pune" --limit-per-city 20
goto end

:scrape_hyderabad
echo.
echo Scraping Hyderabad consulting jobs...
python scrape_consulting_india.py --cities "Hyderabad" --limit-per-city 20
goto end

:scrape_gurugram
echo.
echo Scraping Gurugram/NCR consulting jobs...
python scrape_consulting_india.py --cities "Gurugram" --limit-per-city 20
goto end

:scrape_south
echo.
echo Scraping South India IT corridor...
python scrape_consulting_india.py --cities "Bangalore" "Chennai" "Hyderabad" "Pune" --limit-per-city 15
goto end

:scrape_ncr
echo.
echo Scraping Delhi NCR region...
python scrape_consulting_india.py --cities "Gurugram" "Noida" "New Delhi" --limit-per-city 15
goto end

:scrape_west
echo.
echo Scraping West India...
python scrape_consulting_india.py --cities "Mumbai" "Pune" "Ahmedabad" --limit-per-city 15
goto end

:scrape_high_volume
echo.
echo High volume scan (this will take longer)...
python scrape_consulting_india.py --tier-1-only --limit-per-city 25 --headless False
goto end

:custom_search
echo.
set /p cities="Enter cities (space-separated, e.g., Bangalore Mumbai Pune): "
set /p limit="Enter jobs per city (default 15): "
if "%limit%"=="" set limit=15
python scrape_consulting_india.py --cities %cities% --limit-per-city %limit%
goto end

:headless_off
echo.
echo Running with browser visible...
python scrape_consulting_india.py --headless False --limit-per-city 10
goto end

:no_dedup
echo.
echo Scraping without duplicate check...
python scrape_consulting_india.py --no-dedup --limit-per-city 10
goto end

:check_jobs
echo.
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); print(f'Total consulting jobs: {len(gs.get_all_jobs())}')"
goto end

:view_by_city
echo.
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); cities = {}; [cities.__setitem__(j.get('Search City', 'Unknown'), cities.get(j.get('Search City', 'Unknown'), 0) + 1) for j in jobs]; [print(f'{c}: {count}') for c, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)]"
goto end

:export_csv
echo.
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; import csv; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); f=open('consulting_jobs_india.csv','w',newline='',encoding='utf-8'); w=csv.DictWriter(f,fieldnames=jobs[0].keys()); w.writeheader(); w.writerows(jobs); f.close(); print('Exported to consulting_jobs_india.csv')"
goto end

:find_big4
echo.
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); big4 = ['Deloitte', 'PwC', 'EY', 'KPMG']; [print(f'{j.get(\"Job Title\")} at {j.get(\"Company\")} - {j.get(\"Search City\")}') for j in jobs if any(b in j.get('Company', '') for b in big4)]"
goto end

:find_today
echo.
python -c "from linkedin_scraper.integrations.google_sheets import GoogleSheetsIntegration; gs = GoogleSheetsIntegration(); gs.connect('Consulting_Jobs_India'); jobs = gs.get_all_jobs(); [print(f'{j.get(\"Job Title\")} - {j.get(\"Posted\")} - {j.get(\"Search City\")}') for j in jobs if 'hour' in j.get('Posted', '').lower() or 'minute' in j.get('Posted', '').lower()]"
goto end

:create_session
echo.
echo Creating new LinkedIn session...
python samples\create_session.py
goto end

:show_help
echo.
type CONSULTING_JOBS_COMMANDS.txt | more
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
