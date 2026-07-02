# WhatsApp Bulk Sender

Send the same WhatsApp message to multiple employees using a simple web UI.

**Repository:** https://github.com/officialshafiqahmad/whatsapp-bulk-sender

## Clone and run

```bash
git clone https://github.com/officialshafiqahmad/whatsapp-bulk-sender.git
cd whatsapp-bulk-sender
./start.sh
```

Then open: **http://127.0.0.1:8765**

## For non-technical users

1. Clone the repo (or download from GitHub):
   https://github.com/officialshafiqahmad/whatsapp-bulk-sender
2. Run `./start.sh` or double-click `start.py`
3. Open **http://127.0.0.1:8765** in your browser
4. Type your message, add numbers or import Excel, then click **Send messages**

See **[README_UI.md](README_UI.md)** for full UI instructions and Excel rules.

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
