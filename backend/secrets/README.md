This folder stores cookie files used by `yt-dlp` when platforms require authentication.

- `instagram_cookies.txt`: Netscape-format cookies file used by `yt-dlp` for private Instagram links.
- `youtube_cookies.txt`: Netscape-format cookies file used by `yt-dlp` when YouTube requires sign-in (ex: "confirm you're not a bot").

To trim it down (recommended):

```bash
bash backend/scripts/export_instagram_cookies_from_chrome.sh
```

To generate `youtube_cookies.txt` from a Cookie Editor export:

- Paste your Cookie Editor export into `backend/secrets/youtube_cookies_raw.txt`
- Then run:

```bash
bash backend/scripts/export_youtube_cookies_from_chrome.sh
```

Warning: these files can grant access to your accounts. Handle with care.

