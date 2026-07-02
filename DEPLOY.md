# Deployment — fully online (free)

The app runs as **one public website** on Hugging Face Spaces. No local PC, no tunnel, no payment.

## Live URL

**https://officialshafiqahmad-whatsapp-bulk-sender.hf.space**

## How it works

| Part | Where it runs | Cost |
|------|---------------|------|
| UI | Hugging Face Space | Free |
| Excel import | In your browser | Free |
| WhatsApp sending | HF cloud server | Free |
| QR login | Shown on the web page | Free |

## First-time WhatsApp login

1. Open the live URL
2. Click **Send messages**
3. A QR code appears on the page
4. On your phone: WhatsApp → Settings → Linked Devices → Link a Device
5. Scan the QR code
6. Sending starts automatically

The login is saved on the server until the space restarts (you may need to scan again after long idle periods).

## Deploy or update the online app

```bash
pip install huggingface_hub
huggingface-cli login
./deploy-hf.sh
```

First build takes about 5–10 minutes.

## GitHub Pages (optional mirror)

https://officialshafiqahmad.github.io/whatsapp-bulk-sender/

This is a static copy only. Use the **HF Space URL** above for the full online app.

## Local development (optional)

Only needed if you are changing the code:

```bash
./start.sh
```

## Notes

- Hugging Face free tier may sleep when idle — first visit after sleep can take ~30 seconds to wake up.
- WhatsApp may limit very large bulk sends. Keep the delay at 5+ seconds.
- For official high-volume business messaging, use WhatsApp Business API instead.
