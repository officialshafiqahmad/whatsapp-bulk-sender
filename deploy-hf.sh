#!/bin/bash
set -e
cd "$(dirname "$0")"

SPACE_NAME="${HF_SPACE_NAME:-whatsapp-bulk-sender}"
HF_USER="${HF_USER:-officialshafiqahmad}"
SPACE_REPO="https://huggingface.co/spaces/${HF_USER}/${SPACE_NAME}"

if ! command -v hf >/dev/null 2>&1; then
  echo "Installing huggingface_hub..."
  pip install -U huggingface_hub
fi

if ! hf auth whoami >/dev/null 2>&1; then
  echo "Log in to Hugging Face first:"
  echo "  hf auth login"
  exit 1
fi

echo "Creating/updating Hugging Face Space: ${HF_USER}/${SPACE_NAME}"

hf repo create "$SPACE_NAME" --type space --space_sdk docker --exist-ok || true

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

git archive HEAD | tar -x -C "$TMP_DIR"
cp README.md "$TMP_DIR/README.md"

cd "$TMP_DIR"
git init -q
git add -A
git commit -q -m "Deploy WhatsApp Bulk Sender"
git branch -M main
git remote add space "$SPACE_REPO"
git push -f space main

echo ""
echo "Deployed! Your app will be live at:"
echo "https://${HF_USER}-${SPACE_NAME}.hf.space"
echo ""
echo "First build may take 5-10 minutes."
