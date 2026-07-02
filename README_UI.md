# WhatsApp Bulk Sender

A simple UI tool for sending the same WhatsApp message to many employees. Built for non-technical users.

Unlike `web.whatsapp.com/send/?phone=...&text=...` links, this app **actually sends** each message through WhatsApp Web.

## What the UI includes

1. **Message box** — type the message once
2. **Phone number list** — paste numbers manually (one per line)
3. **Excel import** — upload a `.xlsx` file with **one column only** of phone numbers
4. **Send button** — sends to everyone with live progress

## Quick start (for non-technical users)

1. Open the project folder: `/Users/apple/Development/bulk-message-sender`
2. Double-click **`start.py`**  
   Or run in Terminal:
   ```bash
   ./start.sh
   ```
3. Your browser opens to: **http://127.0.0.1:8765**
4. On first use, scan the WhatsApp QR code in the browser window that appears

## Excel file rules

The import only accepts files that follow these rules:

| Rule | Example |
|------|---------|
| File type must be `.xlsx` | `employees.xlsx` |
| **Only one column** of data | Column A only |
| Each row = one phone number | `923109916330` |
| Optional header row | `phone` in row 1 is OK |
| International format, no `+` | `923109916330` |

**Accepted example (`sample_numbers.example.xlsx`):**

```
phone
923109916330
923001234567
923331112233
```

**Rejected examples:**
- Two columns (name + phone) → rejected
- Text like `abc` in a cell → rejected
- `.csv` or `.xls` files → rejected

## Manual setup

```bash
cd /Users/apple/Development/bulk-message-sender
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python app.py
```

Then open: http://127.0.0.1:8765

## How sending works

1. You enter the message and phone numbers in the UI
2. Click **Send messages**
3. A Chromium browser opens WhatsApp Web (login saved after first scan)
4. The app opens each chat and clicks **Send**
5. Progress and results appear in the UI

## Tips

- Keep the delay at 5+ seconds for large lists
- Use international numbers without `+`
- For official high-volume company messaging, use WhatsApp Business API instead

## Project files

| File | Purpose |
|------|---------|
| `app.py` | Web server |
| `static/` | UI pages |
| `whatsapp_core.py` | Sending logic |
| `excel_import.py` | Excel validation |
| `start.sh` / `start.py` | Easy launcher |
| `sample_numbers.example.xlsx` | Example import file |
