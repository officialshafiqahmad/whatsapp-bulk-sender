# Free deployment (no payment required)

Everything in this project can run for free.

## Public URLs

| What | URL | Cost |
|------|-----|------|
| **Public UI** | https://officialshafiqahmad.github.io/whatsapp-bulk-sender/ | Free |
| **Sender backend** | Free Cloudflare tunnel from your computer | Free |

## How it works

1. **GitHub Pages** hosts the UI publicly (message box, phone list, Excel import).
2. **Excel import runs in the browser** — no backend needed for that.
3. **Sending** runs on your computer via `./start-public.sh`, which creates a free Cloudflare tunnel URL.
4. Paste that tunnel URL into step 1 of the public UI.

No Render, no credit card, no paid hosting.

## For the person who sends messages

```bash
git clone https://github.com/officialshafiqahmad/whatsapp-bulk-sender.git
cd whatsapp-bulk-sender
chmod +x start-public.sh
./start-public.sh
```

The script prints:
- **Public UI** link to share with your team
- **Backend URL** like `https://something.trycloudflare.com` — paste this into the UI

Keep the terminal window open while messages are sending.

## For your team (non-technical)

1. Open: https://officialshafiqahmad.github.io/whatsapp-bulk-sender/
2. Ask the sender for the backend URL and paste it in step 1
3. Type message, add numbers or import Excel
4. Click **Send messages**

## Local-only use (simplest)

If only one person uses it on the same computer:

```bash
./start.sh
```

Open http://127.0.0.1:8765 — everything works without any tunnel.

## GitHub Pages auto-deploy

Every push to `main` updates the public UI automatically.

## Notes

- The Cloudflare tunnel URL changes each time you restart `start-public.sh` (unless you set up a free named tunnel with a Cloudflare account).
- WhatsApp Web login happens on the computer running `start-public.sh`.
- Paid options like Render are optional and not required.
