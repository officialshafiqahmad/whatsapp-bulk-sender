---
title: WhatsApp Bulk Sender
emoji: 💬
colorFrom: green
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# WhatsApp Bulk Sender

Send the same WhatsApp message to multiple employees using a simple web UI — **fully online, no local software needed**.

**Live app:** https://officialshafiqahmad-company-message-sender.hf.space

**Repository:** https://github.com/officialshafiqahmad/whatsapp-bulk-sender

## Use your existing Chrome WhatsApp (no QR in app)

The online Hugging Face app **cannot** use WhatsApp logged in on your computer — it runs on a remote server.

To use your **existing Chrome WhatsApp login** locally:

```bash
# Terminal 1 — use your normal Chrome profile (WhatsApp already logged in)
./start-chrome.sh --use-my-profile

# Terminal 2
./start.sh
```

Open http://127.0.0.1:8765 — click Send, **no QR code**.

## Use the online app (cloud)

1. Open https://officialshafiqahmad-company-message-sender.hf.space
2. Type your message
3. Add phone numbers or import Excel
4. Click **Send messages**
5. Scan the WhatsApp QR code shown on the page (first time only)

No installation. No tunnel. No PC running in the background.

## Excel import rules

- `.xlsx` only
- **Single column** of phone numbers (column A)
- Optional header row (`phone`)
- International format without `+` (e.g. `923109916330`)

Sample file: `sample_numbers.example.xlsx`

## Deploy updates (maintainer)

Hosted free on **Hugging Face Spaces** (Docker):

```bash
pip install -U huggingface_hub
hf auth login
./deploy-hf.sh
```

See **[DEPLOY.md](DEPLOY.md)** for details.

## Local development (optional)

```bash
./start.sh
```

Open http://127.0.0.1:8765

## CLI (optional)

```bash
python sender.py --list employees.csv --message "Your invoice generated"
```
