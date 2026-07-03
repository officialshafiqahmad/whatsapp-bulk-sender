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

export USE_EXISTING_BROWSER=1
export BROWSER_MODE=cdp
export CDP_URL="${CDP_URL:-http://127.0.0.1:9222}"

echo ""
echo "WhatsApp Bulk Sender (uses your Chrome login — no QR in the app)"
echo ""
echo "Before first use:"
echo "  1. Run ./start-chrome.sh in another terminal"
echo "  2. Log in to WhatsApp Web in that Chrome window once"
echo "  3. Keep Chrome open, then use this app"
echo ""
echo "Open: http://127.0.0.1:8765"
echo ""

python app.py
