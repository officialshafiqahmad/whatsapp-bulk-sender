# Deployment

This app has two public URLs:

| URL | What it serves |
|-----|----------------|
| **GitHub Pages (UI)** | https://officialshafiqahmad.github.io/whatsapp-bulk-sender/ |
| **Render (full app)** | https://whatsapp-bulk-sender.onrender.com |

Use the **Render URL** for the complete experience (UI + sending).  
GitHub Pages hosts the frontend and connects to the Render backend API.

## Deploy backend to Render (one-time)

Render requires a payment method on file (free tier still applies — you won't be charged unless you upgrade).

1. Open: https://render.com/deploy?repo=https://github.com/officialshafiqahmad/whatsapp-bulk-sender
2. Connect GitHub, add billing info, and deploy
3. Your live app URL will be: **https://whatsapp-bulk-sender.onrender.com**

Or use the dashboard: https://dashboard.render.com/select-repo?type=blueprint

## Deploy frontend to GitHub Pages (automatic)

Every push to `main` runs `.github/workflows/deploy-pages.yml` and publishes the UI.

To enable Pages the first time:

```bash
gh api repos/officialshafiqahmad/whatsapp-bulk-sender/pages -X POST \
  -f build_type=workflow \
  -f source[branch]=main \
  -f source[path]=/
```

## Optional: set Render URL in GitHub

If your Render service uses a custom domain, set a repo variable:

```bash
gh variable set RENDER_APP_URL --body "https://your-custom-domain.com"
```

## Local vs cloud WhatsApp login

- **Local (`./start.sh`)**: Browser opens visibly; scan QR code on first use.
- **Cloud (Render)**: Runs headless. WhatsApp Web login on a remote server is limited — for production bulk sending, prefer running locally or use WhatsApp Business API.

## Environment variables (Render)

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `10000` | Server port |
| `HEADLESS` | `true` | Run browser without visible window |
| `PUBLIC_APP_URL` | — | Adds your public URL to CORS allowlist |
