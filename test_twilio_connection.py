#!/usr/bin/env python3
"""
Quick Twilio Connection Test
=============================
Tests your Twilio WhatsApp configuration before running the full automation.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("="*70)
print("TWILIO WHATSAPP CONNECTION TEST")
print("="*70)
print()

# Check environment variables
print("[1/5] Checking environment variables...")
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
from_number = os.getenv('TWILIO_WHATSAPP_FROM')
to_number = os.getenv('WHATSAPP_TO')

if not account_sid:
    print("❌ TWILIO_ACCOUNT_SID not found in .env")
    sys.exit(1)
if not auth_token or auth_token == 'your_auth_token_here':
    print("❌ TWILIO_AUTH_TOKEN not set in .env")
    print("   Please add your Auth Token to .env file")
    sys.exit(1)
if not from_number:
    print("❌ TWILIO_WHATSAPP_FROM not found in .env")
    sys.exit(1)
if not to_number:
    print("❌ WHATSAPP_TO not found in .env")
    sys.exit(1)

print(f"✅ Account SID: {account_sid[:10]}...")
print(f"✅ Auth Token: {'*' * 20} (hidden)")
print(f"✅ From: {from_number}")
print(f"✅ To: {to_number}")
print()

# Check Twilio library
print("[2/5] Checking Twilio library...")
try:
    from twilio.rest import Client
    import twilio
    print(f"✅ Twilio library installed (version {twilio.__version__})")
except ImportError:
    print("❌ Twilio library not installed")
    print("   Run: pip install twilio")
    sys.exit(1)
print()

# Initialize Twilio client
print("[3/5] Initializing Twilio client...")
try:
    client = Client(account_sid, auth_token)
    print("✅ Twilio client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Twilio client: {e}")
    sys.exit(1)
print()

# Verify account
print("[4/5] Verifying Twilio account...")
try:
    account = client.api.accounts(account_sid).fetch()
    print(f"✅ Account verified: {account.friendly_name}")
    print(f"   Status: {account.status}")
except Exception as e:
    print(f"❌ Failed to verify account: {e}")
    print("   Check your Account SID and Auth Token")
    sys.exit(1)
print()

# Send test message
print("[5/5] Sending test WhatsApp message...")
print("   This will send a real message to your WhatsApp!")
print()

response = input("   Send test message? (yes/no): ")
if response.lower() != 'yes':
    print("   Skipped test message")
    print()
    print("="*70)
    print("✅ CONNECTION TEST PASSED")
    print("="*70)
    print()
    print("Your Twilio configuration is correct!")
    print()
    print("Next steps:")
    print("1. Run: python whatsapp_notifier.py --test")
    print("2. Run: python whatsapp_notifier.py --force")
    print("3. Run: setup_whatsapp_automation.bat (as Admin)")
    sys.exit(0)

try:
    message = client.messages.create(
        from_=from_number,
        body="🎉 Test successful! Your WhatsApp automation is ready to go!",
        to=to_number
    )
    print(f"✅ Message sent successfully!")
    print(f"   Message SID: {message.sid}")
    print(f"   Status: {message.status}")
except Exception as e:
    print(f"❌ Failed to send message: {e}")
    print()
    print("Common issues:")
    print("- Make sure you joined the Twilio sandbox")
    print("- Check your WhatsApp number format")
    print("- Verify Auth Token is correct")
    sys.exit(1)

print()
print("="*70)
print("✅ ALL TESTS PASSED!")
print("="*70)
print()
print("Your Twilio WhatsApp integration is working perfectly!")
print()
print("Next steps:")
print("1. Run: python whatsapp_notifier.py --test")
print("2. Run: python whatsapp_notifier.py --force")
print("3. Run: setup_whatsapp_automation.bat (as Admin)")
print()
