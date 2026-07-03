#!/bin/bash
set -e
cd "$(dirname "$0")"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEBUG_PORT="${CDP_PORT:-9222}"
PROFILE_DIR="${HOME}/.chrome-whatsapp-sender"

if [ ! -x "$CHROME" ]; then
  echo "Google Chrome not found at: $CHROME"
  exit 1
fi

if [ "${1:-}" = "--use-my-profile" ]; then
  echo ""
  echo "Use your existing Chrome WhatsApp login"
  echo "========================================"
  echo "1. Quit Chrome completely (Cmd+Q)"
  echo "2. Press Enter here"
  read -r
  echo ""
  echo "Starting Chrome with your normal profile..."
  echo "Then run ./start.sh in another terminal."
  echo ""
  exec "$CHROME" --remote-debugging-port="$DEBUG_PORT" "https://web.whatsapp.com"
fi

mkdir -p "$PROFILE_DIR"

echo ""
echo "Starting Chrome for WhatsApp Bulk Sender"
echo "========================================"
echo "1. Log in to WhatsApp Web in the Chrome window (only once)."
echo "2. Keep Chrome open."
echo "3. Run ./start.sh in another terminal."
echo ""
echo "Already logged in to WhatsApp in your normal Chrome?"
echo "  Quit Chrome (Cmd+Q), then run:"
echo "  ./start-chrome.sh --use-my-profile"
echo ""

exec "$CHROME" \
  --remote-debugging-port="$DEBUG_PORT" \
  --user-data-dir="$PROFILE_DIR" \
  "https://web.whatsapp.com"
