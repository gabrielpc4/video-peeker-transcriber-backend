import argparse
import datetime as dt
import re
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NetscapeCookie:
    domain: str
    include_subdomains: str
    path: str
    secure: str
    expires: str
    name: str
    value: str

    def to_line(self) -> str:
        return "\t".join([self.domain, self.include_subdomains, self.path, self.secure, self.expires, self.name, self.value])


_ISO_LIKE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T")


def _parse_expires_to_epoch(text: str) -> int:
    t = (text or "").strip()
    if t == "" or t.lower() == "session":
        return 0

    # Already epoch?
    try:
        return int(float(t))
    except Exception:
        pass

    if _ISO_LIKE_RE.match(t):
        try:
            if t.endswith("Z"):
                t = t[:-1] + "+00:00"
            parsed = dt.datetime.fromisoformat(t)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=dt.timezone.utc)
            return int(parsed.timestamp())
        except Exception:
            return 0

    return 0


def _parse_cookie_editor_row(raw: str) -> tuple[NetscapeCookie, bool] | None:
    """
    Parse a Cookie-Editor style export row:
      name <tab> value <tab> domain <tab> path <tab> expiresISO/Session <tab> size <tab> httpOnly? <tab> secure? ...

    Returns (cookie, is_http_only).
    """
    text = raw.strip()
    if text == "" or text.startswith("#"):
        return None

    parts = [p for p in text.split("\t") if p != ""]
    if len(parts) < 5:
        parts = text.split()
    if len(parts) < 5:
        return None

    name = parts[0].strip()
    value = parts[1].strip()
    domain = parts[2].strip()
    path = parts[3].strip() or "/"
    expires_raw = parts[4].strip()

    if name == "" or domain == "":
        return None

    include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"

    # Cookie Editor typically has: [5]=size, [6]=httpOnly, [7]=secure
    http_only = (len(parts) >= 7 and parts[6].strip() == "✓")
    secure = "TRUE" if (len(parts) >= 8 and parts[7].strip() == "✓") else "FALSE"

    expires_epoch = _parse_expires_to_epoch(expires_raw)

    cookie = NetscapeCookie(
        domain=domain,
        include_subdomains=include_subdomains,
        path=path,
        secure=secure,
        expires=str(expires_epoch),
        name=name,
        value=value,
    )
    return cookie, http_only


def convert(
    *,
    input_path: Path,
    output_path: Path,
    keep_expired: bool,
) -> None:
    raw_lines = input_path.read_text(encoding="utf-8", errors="replace").splitlines()

    now_epoch = int(time.time())
    cookies: list[str] = []

    for raw in raw_lines:
        parsed = _parse_cookie_editor_row(raw)
        if parsed is None:
            continue
        cookie, http_only = parsed

        if keep_expired is False:
            try:
                exp = int(cookie.expires)
            except Exception:
                exp = 0
            if exp != 0 and exp < now_epoch:
                continue

        domain_out = cookie.domain
        if http_only:
            # Netscape convention for HttpOnly cookies.
            domain_out = "#HttpOnly_" + domain_out

        cookies.append(
            NetscapeCookie(
                domain=domain_out,
                include_subdomains=cookie.include_subdomains,
                path=cookie.path,
                secure=cookie.secure,
                expires=cookie.expires,
                name=cookie.name,
                value=cookie.value,
            ).to_line()
        )

    # Stable sort for diffs.
    cookies.sort(key=lambda line: line.split("\t")[0].lstrip("#HttpOnly_").lstrip(".").lower() + "\t" + line)

    out_lines: list[str] = []
    out_lines.append("# Netscape HTTP Cookie File\n")
    out_lines.append("# Generated from backend/secrets/www.youtube.com export\n")
    out_lines.append("# This file is used by yt-dlp via --cookies\n")
    out_lines.append("\n")
    for line in cookies:
        out_lines.append(line + "\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(out_lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert backend/secrets/www.youtube.com export to Netscape youtube_cookies.txt.")
    parser.add_argument("--in", dest="input_path", required=True, help="Input export file (tab-separated)")
    parser.add_argument("--out", dest="output_path", required=True, help="Output Netscape cookies.txt path")
    parser.add_argument("--keep-expired", action="store_true", help="Keep expired cookies (not recommended).")
    args = parser.parse_args()

    convert(
        input_path=Path(args.input_path).expanduser().resolve(),
        output_path=Path(args.output_path).expanduser().resolve(),
        keep_expired=bool(args.keep_expired),
    )

