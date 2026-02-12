import time
from dataclasses import dataclass
from pathlib import Path


ALLOWED_DOMAIN_SUFFIXES = (
    "instagram.com",
    "cdninstagram.com",
    "facebook.com",
    "fbcdn.net",
)


@dataclass(frozen=True)
class CookieLine:
    domain: str
    include_subdomains: str
    path: str
    secure: str
    expires: str
    name: str
    value: str

    @property
    def key(self) -> tuple[str, str, str]:
        return (self.domain, self.path, self.name)

    def expires_epoch(self) -> int | None:
        try:
            return int(self.expires)
        except Exception:
            return None

    def is_expired(self, now_epoch: int) -> bool:
        epoch = self.expires_epoch()
        if epoch is None:
            return False
        if epoch == 0:
            return False  # session cookie in Netscape format
        return epoch < now_epoch

    def to_netscape_line(self) -> str:
        return "\t".join([self.domain, self.include_subdomains, self.path, self.secure, self.expires, self.name, self.value])


def _allowed_domain(domain: str) -> bool:
    d = domain.lstrip(".").lower()
    return any(d.endswith(suffix) for suffix in ALLOWED_DOMAIN_SUFFIXES)


def _parse_cookie_line(raw: str) -> CookieLine | None:
    parts = raw.rstrip("\n").split("\t")
    if len(parts) < 7:
        return None
    return CookieLine(
        domain=parts[0],
        include_subdomains=parts[1],
        path=parts[2],
        secure=parts[3],
        expires=parts[4],
        name=parts[5],
        value="\t".join(parts[6:]),
    )


def trim_file(input_path: Path, output_path: Path) -> None:
    if input_path.exists() is False:
        raise SystemExit(f"Input file not found: {input_path}")

    raw_lines = input_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    header_lines: list[str] = []
    cookie_lines: list[CookieLine] = []

    for line in raw_lines:
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
            continue

        cookie = _parse_cookie_line(line)
        if cookie is None:
            continue

        if _allowed_domain(cookie.domain) is False:
            continue

        cookie_lines.append(cookie)

    now_epoch = int(time.time())

    # Deduplicate: keep the newest expiry per (domain, path, name).
    chosen: dict[tuple[str, str, str], CookieLine] = {}
    for cookie in cookie_lines:
        if cookie.is_expired(now_epoch):
            continue

        existing = chosen.get(cookie.key)
        if existing is None:
            chosen[cookie.key] = cookie
            continue

        existing_exp = existing.expires_epoch() or 0
        cookie_exp = cookie.expires_epoch() or 0
        if cookie_exp >= existing_exp:
            chosen[cookie.key] = cookie

    # Stable sort for diffs.
    kept = list(chosen.values())
    kept.sort(key=lambda c: (c.domain.lstrip(".").lower(), c.path, c.name))

    output_lines: list[str] = []
    if len(header_lines) == 0:
        output_lines.append("# Netscape HTTP Cookie File\n")
    else:
        output_lines.extend(header_lines)

    for cookie in kept:
        output_lines.append(cookie.to_netscape_line() + "\n")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("".join(output_lines), encoding="utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Trim a Netscape cookies.txt to only Instagram/Facebook related domains and remove duplicates/expired.")
    parser.add_argument("--in", dest="input_path", required=True, help="Input cookies.txt path")
    parser.add_argument("--out", dest="output_path", required=True, help="Output cookies.txt path")
    parser.add_argument("--in-place", action="store_true", help="Overwrite input file (keeps a .bak copy)")
    args = parser.parse_args()

    input_path = Path(args.input_path).expanduser().resolve()
    output_path = Path(args.output_path).expanduser().resolve()

    if args.in_place:
        backup_path = input_path.with_suffix(input_path.suffix + ".bak")
        backup_path.write_bytes(input_path.read_bytes())
        trim_file(input_path=backup_path, output_path=input_path)
    else:
        trim_file(input_path=input_path, output_path=output_path)
