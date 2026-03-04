FROM python:3.12-slim

WORKDIR /app

# System deps needed by yt-dlp + ffmpeg pipeline
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# JS runtime for yt-dlp EJS (recommended)
# Minimum supported Deno version (per yt-dlp docs): 2.0.0
RUN set -e; \
    arch="$(uname -m)"; \
    if [ "$arch" = "x86_64" ]; then deno_arch="x86_64-unknown-linux-gnu"; \
    elif [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then deno_arch="aarch64-unknown-linux-gnu"; \
    else echo "Unsupported arch for deno: $arch" && exit 1; fi; \
    url="https://github.com/denoland/deno/releases/download/v2.0.0/deno-${deno_arch}.zip"; \
    curl -fsSL "$url" -o /tmp/deno.zip; \
    unzip -q /tmp/deno.zip -d /usr/local/bin; \
    chmod +x /usr/local/bin/deno; \
    rm -f /tmp/deno.zip

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install yt-dlp with default extras, including yt-dlp-ejs scripts
RUN pip install --no-cache-dir "yt-dlp[default]"

COPY app /app/app
COPY secrets /app/secrets

EXPOSE 8000

CMD ["python", "-m", "app.serve"]

