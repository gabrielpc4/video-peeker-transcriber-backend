This folder is for **local secrets** (not committed to git).

- `instagram_cookies.txt`: Netscape-format cookies file used by `yt-dlp` for private Instagram links.

To trim it down (recommended):

```bash
bash backend/scripts/export_instagram_cookies_from_chrome.sh
```

Do not commit this file.

