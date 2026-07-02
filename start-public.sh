#!/bin/bash
set -e
cd "$(dirname "$0")"

PORT="${PORT:-8765}"

if [ ! -d "venv" ]; then
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  playwright install chromium
else
  source venv/bin/activate
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "Installing cloudflared (free public tunnel, no payment required)..."
  if command -v brew >/dev/null 2>&1; then
    brew install cloudflared
  else
    echo "Please install cloudflared manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    exit 1
  fi
fi

echo ""
echo "Starting WhatsApp Bulk Sender with a free public URL..."
echo "Local app: http://127.0.0.1:${PORT}"
echo ""

python app.py &
APP_PID=$!

cleanup() {
  kill "$APP_PID" 2>/dev/null || true
  kill "$TUNNEL_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 2

TUNNEL_LOG="$(mktemp)"
cloudflared tunnel --url "http://127.0.0.1:${PORT}" 2>&1 | tee "$TUNNEL_LOG" &
TUNNEL_PID=$!

PUBLIC_URL=""
for _ in $(seq 1 30); do
  PUBLIC_URL="$(grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' "$TUNNEL_LOG" | head -1 || true)"
  if [ -n "$PUBLIC_URL" ]; then
    break
  fi
  sleep 1
done

echo ""
echo "=============================================="
echo "Public UI (share with your team):"
echo "https://officialshafiqahmad.github.io/whatsapp-bulk-sender/"
echo ""
if [ -n "$PUBLIC_URL" ]; then
  echo "Public backend URL (paste in step 1 of the UI):"
  echo "$PUBLIC_URL"
else
  echo "Backend tunnel is starting. Check the cloudflared output above for your trycloudflare.com URL."
fi
echo "=============================================="
echo ""
echo "Keep this window open while sending messages."
echo ""

wait "$TUNNEL_PID"
