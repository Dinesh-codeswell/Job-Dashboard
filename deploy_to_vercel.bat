@echo off
REM ================================================================================
REM                    Vercel Deployment Script
REM ================================================================================

echo.
echo ================================================================================
echo                    Consulting Jobs Dashboard - Vercel Deploy
echo ================================================================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo Node.js found: 
node --version
echo.

REM Check if Vercel CLI is installed
where vercel >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Vercel CLI not found. Installing...
    echo.
    npm i -g vercel
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install Vercel CLI
        pause
        exit /b 1
    )
)

echo Vercel CLI version:
vercel --version
echo.

REM Check if we're in the right directory
if not exist "vercel.json" (
    echo ERROR: vercel.json not found!
    echo Please run this script from the project root directory.
    echo.
    pause
    exit /b 1
)

REM Check if credentials exist
if not exist "credentials.json" (
    echo.
    echo WARNING: credentials.json not found!
    echo The deployment will fail without Google Sheets credentials.
    echo.
    set /p upload_creds="Do you want to continue anyway? (Y/N): "
    if /i "%upload_creds%" NEQ "Y" (
        echo Deployment cancelled.
        pause
        exit /b 1
    )
)

echo.
echo ================================================================================
echo  Starting Vercel Deployment...
echo ================================================================================
echo.

REM Login to Vercel
echo Step 1: Vercel Login
echo ---------------------
vercel login
echo.

REM Deploy to preview
echo Step 2: Deploy to Preview
echo -------------------------
echo This will create a preview deployment...
echo.
vercel --yes
echo.

REM Ask if user wants to deploy to production
set /p deploy_prod="Do you want to deploy to production? (Y/N): "
if /i "%deploy_prod%"=="Y" (
    echo.
    echo Step 3: Deploy to Production
    echo ----------------------------
    vercel --prod --yes
)

echo.
echo ================================================================================
echo  Deployment Complete!
echo ================================================================================
echo.
echo Next Steps:
echo 1. Go to your Vercel dashboard
echo 2. Add environment variables (see VERCEL_DEPLOYMENT.md)
echo 3. Upload credentials.json if not already done
echo 4. Redeploy if needed
echo.
echo Your dashboard URL will be: https://your-project.vercel.app
echo.
pause
