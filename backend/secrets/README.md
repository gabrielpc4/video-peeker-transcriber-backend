This folder is for **local secrets** (not committed to git).

- `instagram_cookies.txt`: Netscape-format cookies file used by `yt-dlp` for private Instagram links.

To generate it from your current Chrome session (macOS):

```bash
bash backend/scripts/export_instagram_cookies_from_chrome.sh
```

Do not commit this file.

