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
RUN curl -fsSL https://deno.land/install.sh | sh -s v2.0.0
ENV DENO_INSTALL=/root/.deno
ENV PATH="$DENO_INSTALL/bin:$PATH"

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install yt-dlp with default extras, including yt-dlp-ejs scripts
RUN pip install --no-cache-dir "yt-dlp[default]"

COPY app /app/app
COPY secrets /app/secrets

EXPOSE 8000

CMD ["sh", "-lc", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

