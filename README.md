# WhatsApp Bulk Sender

Send the same WhatsApp message to multiple employees using a simple web UI.

**Repository:** https://github.com/officialshafiqahmad/whatsapp-bulk-sender

**Public UI (free):** https://officialshafiqahmad.github.io/whatsapp-bulk-sender/

## 100% free setup

| Part | How | Payment |
|------|-----|---------|
| UI | GitHub Pages | Free |
| Excel import | Runs in browser | Free |
| Sending | `./start-public.sh` + Cloudflare tunnel | Free |

See **[DEPLOY.md](DEPLOY.md)** for the full free setup guide.

## Quick start for sender

```bash
git clone https://github.com/officialshafiqahmad/whatsapp-bulk-sender.git
cd whatsapp-bulk-sender
./start-public.sh
```

1. Share the **public UI** link with your team
2. Paste the **backend URL** (from the script) into step 1 of the UI
3. Send messages

## Local-only (one computer)

```bash
./start.sh
```

Open http://127.0.0.1:8765

## For your team

1. Open https://officialshafiqahmad.github.io/whatsapp-bulk-sender/
2. Paste the backend URL from the person running `start-public.sh`
3. Type message, add numbers or import Excel, click **Send messages**

See **[README_UI.md](README_UI.md)** for UI instructions and Excel rules.

## Excel import rules

- `.xlsx` only
- **Single column** of phone numbers (column A)
- Optional header row (`phone`)
- International format without `+` (e.g. `923109916330`)

Sample file: `sample_numbers.example.xlsx`

## Technical setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python app.py
```

## CLI (optional)

```bash
python sender.py --list employees.csv --message "Your invoice generated"
```
