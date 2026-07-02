#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  playwright install chromium
else
  source venv/bin/activate
fi

echo ""
echo "Starting WhatsApp Bulk Sender..."
echo "Open this in your browser: http://127.0.0.1:8765"
echo ""

python app.py
