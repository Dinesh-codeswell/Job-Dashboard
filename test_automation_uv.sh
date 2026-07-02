#!/bin/bash
# Test WhatsApp automation using UV

echo "Testing WhatsApp automation (dry run)..."
uv run python whatsapp_notifier.py --test
