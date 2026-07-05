#!/usr/bin/env python

"""Download or convert an image to WebP and record it in attribution.json."""

import argparse
import json
import requests
import subprocess
import tempfile
from pathlib import Path

DEFAULT_OUT_DIR = Path("app/img/djt")
DEFAULT_ATTRIBUTION = DEFAULT_OUT_DIR / "attribution.json"
DEFAULT_QUALITY = 85


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="Source image URL to download")
    source.add_argument("--file", type=Path, help="Local image file to convert")
    p.add_argument("--stem", required=True, help="Output filename stem, e.g. gs_arizona-rally_20160319")
    p.add_argument("--outlet", required=True, help="Publisher or source name")
    p.add_argument("--title", required=True, help="Image title or caption")
    p.add_argument("--date", default=None, help="ISO date YYYY-MM-DD (omit if unknown)")
    p.add_argument("--photographer", default=None)
    p.add_argument("--license", default=None, help="License string, e.g. 'CC BY-SA 3.0'")
    p.add_argument("--source-url", default=None, help="Canonical page URL for attribution")
    p.add_argument("--quality", type=int, default=DEFAULT_QUALITY, help="cwebp quality 0-100")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    p.add_argument("--attribution", type=Path, default=DEFAULT_ATTRIBUTION)
    return p.parse_args()


def download(url: str, dest: Path) -> None:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; download_image/1.0)"}
    resp = requests.get(url, headers=headers, timeout=30, stream=True)
    resp.raise_for_status()
    with dest.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=65536):
            fh.write(chunk)


def convert_to_webp(src: Path, dest: Path, quality: int) -> None:
    result = subprocess.run(
        ["cwebp", "-q", str(quality), str(src), "-o", str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr)
        raise SystemExit(f"cwebp failed with exit code {result.returncode}")


def update_attribution(attr_path: Path, entry: dict) -> None:
    if attr_path.exists():
        data = json.loads(attr_path.read_text())
    else:
        data = {"images": []}
    data.setdefault("images", [])
    data["images"].append(entry)
    attr_path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"{args.stem}.webp"

    if args.file:
        src = args.file.resolve()
        if not src.exists():
            raise SystemExit(f"File not found: {src}")
        print(f"Converting {src}")
        convert_to_webp(src, out_path, args.quality)
        print(f"Saved {out_path}")
    else:
        suffix = Path(args.url.split("?")[0]).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            print(f"Downloading {args.url}")
            download(args.url, tmp_path)
            convert_to_webp(tmp_path, out_path, args.quality)
            print(f"Saved {out_path}")
        finally:
            tmp_path.unlink(missing_ok=True)

    entry: dict = {
        "file": f"{args.stem}.webp",
        "outlet": args.outlet,
        "title": args.title,
        "date": args.date,
    }
    if args.photographer:
        entry["photographer"] = args.photographer
    if args.license:
        entry["license"] = args.license
    if args.source_url:
        entry["source_url"] = args.source_url

    update_attribution(args.attribution, entry)
    print(f"Updated {args.attribution}")


if __name__ == "__main__":
    main()
