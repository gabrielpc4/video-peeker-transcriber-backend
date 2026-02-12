# VideoPeek

iOS app that lets you share:

- an audio file (e.g. WhatsApp voice note)
- a YouTube link
- an Instagram post/reel link

Then:

1) transcribe with AssemblyAI (full transcript; Portuguese or English)
2) generate a breakdown with Claude that captures the vibe and skips fluff

## Backend

This repo includes a small backend under `backend/` that:

- downloads media with `yt-dlp` (Instagram private via cookies)
- extracts audio with `ffmpeg`
- calls AssemblyAI for transcription (language detection)
- calls Anthropic Claude for breakdown (structured output)

### Requirements

- Python 3.11+
- `ffmpeg`
- `yt-dlp`

### Setup

Create `backend/.env`:

```bash
ASSEMBLYAI_API_KEY="..."
ANTHROPIC_API_KEY="..."
```

For private Instagram content, export cookies (Netscape format) to:

`backend/secrets/instagram_cookies.txt`

### Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

## iOS

Open `VideoPeek.xcodeproj` and run the app.

