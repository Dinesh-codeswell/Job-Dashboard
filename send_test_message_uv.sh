#!/bin/bash
# Send test WhatsApp messages using UV

echo "Sending test WhatsApp messages..."
uv run python whatsapp_notifier.py --force
