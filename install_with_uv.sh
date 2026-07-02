#!/bin/bash
# Install WhatsApp dependencies using UV package manager

echo "============================================================================"
echo "Installing WhatsApp Notification Dependencies (UV)"
echo "============================================================================"
echo ""

echo "[1/3] Installing Twilio..."
uv pip install twilio
if [ $? -eq 0 ]; then
    echo "✅ Twilio installed"
else
    echo "❌ Failed to install Twilio with UV"
    echo ""
    echo "Trying alternative method (virtual environment)..."
    
    # Create virtual environment
    py -m venv venv
    source venv/Scripts/activate
    pip install twilio
    
    if [ $? -eq 0 ]; then
        echo "✅ Twilio installed in virtual environment"
        echo ""
        echo "⚠️  IMPORTANT: You need to activate the virtual environment before running scripts:"
        echo "   source venv/Scripts/activate"
    else
        echo "❌ Failed to install Twilio"
        exit 1
    fi
fi
echo ""

echo "[2/3] Installing other dependencies..."
uv pip install requests python-dotenv gspread google-auth 2>/dev/null || pip install requests python-dotenv gspread google-auth
echo "✅ Dependencies installed"
echo ""

echo "[3/3] Verifying installation..."
py -c "import twilio; print(f'✅ Twilio version: {twilio.__version__}')" 2>/dev/null
if [ $? -ne 0 ]; then
    python -c "import twilio; print(f'✅ Twilio version: {twilio.__version__}')" 2>/dev/null
fi
echo ""

echo "============================================================================"
echo "Installation Complete!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "1. Add your Auth Token to .env file"
echo "2. Run: py test_twilio_connection.py"
echo "3. Run: py whatsapp_notifier.py --test"
echo ""
