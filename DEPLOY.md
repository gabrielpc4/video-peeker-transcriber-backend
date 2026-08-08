## Deploy (Render)

Render is the most plug-and-play option: connect the GitHub repo and it builds/runs automatically.

### 1) Create the service

- Go to Render → **New** → **Blueprint**
- Select this repo: `gabrielpc4/video-transcriber-backend`
- Render will pick up `render.yaml`

### 2) Add required env vars (keys)

In the Render service settings, set:

- `ASSEMBLYAI_API_KEY`
- `ANTHROPIC_API_KEY`

### 3) Use it from iOS

Render gives you a URL like `https://video-transcriber-backend.onrender.com`.
Use that as the backend base URL in the iOS app settings.

## Deploy (VPS, fixed monthly cost)

This backend can also be deployed on any VPS with a **fixed monthly price** (e.g. Hetzner, DigitalOcean, Linode).
You only pay the monthly VM price (plus whatever bandwidth/storage your provider charges).

### 1) Server prerequisites

On an Ubuntu server:

- Install Docker + Docker Compose plugin
- Open port **8000** (or put it behind a reverse proxy)

### 2) Deploy

```bash
git clone git@github.com:gabrielpc4/video-transcriber-backend.git
cd video-transcriber-backend
mkdir -p data
docker compose up -d --build
```

Backend will be available at:

- `http://<server-ip>:8000`

### 3) Recommended: HTTPS + domain

Put a reverse proxy (Caddy or Nginx) in front of port 8000 and enable HTTPS.
