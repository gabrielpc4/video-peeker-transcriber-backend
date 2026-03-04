This folder stores cookie files used by `yt-dlp` when platforms require authentication.

- `instagram_cookies.txt`: Netscape-format cookies file used by `yt-dlp` for private Instagram links.
- `youtube_cookies.txt`: Netscape-format cookies file used by `yt-dlp` when YouTube requires sign-in (ex: "confirm you're not a bot").

Preferred way to refresh YouTube cookies:

- Open the iOS app `Settings`
- Tap `Atualizar cookies do YouTube (login no iPhone)`
- Log in with the account you want to use (for example `gabrielgpk5@gmail.com`) inside the in-app web session
- Tap `Capturar e enviar`

This sends only the current device web session cookies to backend endpoint `POST /youtube-cookies/upload`, and rewrites `youtube_cookies.txt`.

To trim it down (recommended):

```bash
bash backend/scripts/export_instagram_cookies_from_chrome.sh
```

To generate `youtube_cookies.txt` from a Cookie Editor export:

- Paste your Cookie Editor export into `backend/secrets/www.youtube.com`
- Then run:

```bash
bash backend/scripts/make_youtube_cookies_from_domain_export.sh
```

Warning: these files can grant access to your accounts. Handle with care.

