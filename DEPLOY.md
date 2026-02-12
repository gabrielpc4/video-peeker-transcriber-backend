## Deploy (fixed monthly cost)

This backend can be deployed on any VPS with a **fixed monthly price** (e.g. Hetzner, DigitalOcean, Linode).
You only pay the monthly VM price (plus whatever bandwidth/storage your provider charges).

### 1) Server prerequisites

On an Ubuntu server:

- Install Docker + Docker Compose plugin
- Open port **8000** (or put it behind a reverse proxy)

### 2) Deploy

```bash
git clone git@github.com:gabrielpc4/VibeRecap.git videopeek
cd videopeek
mkdir -p backend/data
docker compose up -d --build
```

Backend will be available at:

- `http://<server-ip>:8000`

### 3) Recommended: HTTPS + domain

Put a reverse proxy (Caddy or Nginx) in front of port 8000 and enable HTTPS.

