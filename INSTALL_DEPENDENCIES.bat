@echo off
REM ============================================================================
REM Install WhatsApp Notification Dependencies
REM ============================================================================

echo.
echo ============================================================================
echo Installing WhatsApp Notification Dependencies
echo ============================================================================
echo.

echo [1/2] Installing Twilio library...

REM Try multiple methods to install
pip install twilio >nul 2>&1
if %errorLevel% equ 0 (
    echo OK - Twilio installed via pip
    goto verify
)

python -m pip install twilio >nul 2>&1
if %errorLevel% equ 0 (
    echo OK - Twilio installed via python -m pip
    goto verify
)

py -m pip install twilio >nul 2>&1
if %errorLevel% equ 0 (
    echo OK - Twilio installed via py -m pip
    goto verify
)

echo ERROR: Failed to install Twilio
echo.
echo Please run manually:
echo   py -m pip install twilio
echo.
pause
exit /b 1

:verify
echo.

echo [2/2] Verifying installation...

REM Try multiple Python commands
python -c "import twilio; print(f'Twilio version: {twilio.__version__}')" 2>nul
if %errorLevel% equ 0 goto verified

py -c "import twilio; print(f'Twilio version: {twilio.__version__}')" 2>nul
if %errorLevel% equ 0 goto verified

echo WARNING: Could not verify Twilio installation
goto done

:verified
echo OK - Twilio verified

:done
echo.

echo ============================================================================
echo Installation Complete!
echo ============================================================================
echo.
echo Next steps:
echo 1. Add your Auth Token to .env file
echo 2. Run: python whatsapp_notifier.py --test
echo.
pause
