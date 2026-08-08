# Video Transcriber Backend

This is the backend that works for the iOS app, that lets you share:

- an audio file (e.g. WhatsApp voice note)
- a YouTube link
- an Instagram post/reel link

Then:

1. transcribe with AssemblyAI (full transcript; Portuguese or English)
2. generate a breakdown with Claude that captures the vibe and skips fluff

## Backend

- downloads media with `yt-dlp` (Instagram private via cookies)
- extracts audio with `ffmpeg`
- calls AssemblyAI for transcription (language detection)
- calls Anthropic Claude for breakdown (structured output)

### Requirements

- Python 3.11+
- `ffmpeg`
- `yt-dlp`

### Setup

Set the required API keys as environment variables before starting the server:

```bash
export ASSEMBLYAI_API_KEY="your-assemblyai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

For private Instagram content, export cookies (Netscape format) to:

`secrets/instagram_cookies.txt`

### Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## License

This project is licensed under the [MIT License](LICENSE).
