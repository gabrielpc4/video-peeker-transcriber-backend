FROM python:3.12-slim

WORKDIR /app

# System deps needed by yt-dlp + ffmpeg pipeline
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# yt-dlp as a separate install (keeps requirements.txt simple)
RUN pip install --no-cache-dir yt-dlp

COPY app /app/app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

