#!/usr/bin/env python3
"""Loopback-only static server and read-only GitHub GeoJSON proxy."""

from __future__ import annotations

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
REPO_ROOT = APP_DIR.parents[1]
OWNER = os.environ.get("GNSS_DATA_OWNER", "MAKAKAIglitch").strip()
REPO = os.environ.get("GNSS_DATA_REPO", "ggns-drift-atlas").strip()
BRANCH = os.environ.get("GNSS_DATA_BRANCH", "main").strip()
RAW_BASE = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/"
MAX_REMOTE_BYTES = 10 * 1024 * 1024


def _safe_dataset_path(raw_path: str) -> str:
    """Allow only relative GeoJSON paths under data/; prevent traversal/SSRF."""
    path = PurePosixPath(raw_path)
    if path.is_absolute() or ".." in path.parts or "\\" in raw_path:
        raise ValueError("Invalid dataset path")
    if not path.parts or path.parts[0] != "data" or path.suffix.lower() != ".geojson":
        raise ValueError("Only data/*.geojson files are allowed")
    return path.as_posix()


def _read_remote(relative_path: str) -> bytes:
    request = Request(
        RAW_BASE + relative_path,
        headers={
            "User-Agent": "GNSS-Drift-Atlas-local-editor/0.1",
            "Accept": "application/geo+json, application/json, text/plain",
        },
    )
    with urlopen(request, timeout=8) as response:
        data = response.read(MAX_REMOTE_BYTES + 1)
    if len(data) > MAX_REMOTE_BYTES:
        raise ValueError("Remote file exceeds the 10 MiB editor limit")
    return data


def _read_local(relative_path: str) -> bytes:
    target = (REPO_ROOT / relative_path).resolve()
    if REPO_ROOT.resolve() not in target.parents:
        raise ValueError("Invalid local path")
    return target.read_bytes()


def read_catalog() -> tuple[bytes, str]:
    try:
        return _read_remote("catalog.json"), "github"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return _read_local("catalog.json"), "local"


def read_dataset(relative_path: str) -> tuple[bytes, str]:
    safe_path = _safe_dataset_path(relative_path)
    try:
        return _read_remote(safe_path), "github"
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return _read_local(safe_path), "local"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()

    def _send_bytes(self, payload: bytes, content_type: str, source: str | None = None) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        if source:
            self.send_header("X-Atlas-Source", source)
        self.end_headers()
        self.wfile.write(payload)

    def _send_error_json(self, status: int, message: str) -> None:
        payload = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        parsed = urlparse(self.path)
        if parsed.path == "/api/catalog":
            try:
                payload, source = read_catalog()
                json.loads(payload.decode("utf-8"))
                self._send_bytes(payload, "application/json; charset=utf-8", source)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, HTTPError, URLError, ValueError) as exc:
                self._send_error_json(502, f"Could not load catalog: {exc}")
            return

        if parsed.path == "/api/data":
            params = parse_qs(parsed.query)
            requested = params.get("path", [""])[0]
            try:
                payload, source = read_dataset(requested)
                data = json.loads(payload.decode("utf-8"))
                if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list):
                    raise ValueError("Dataset is not a GeoJSON FeatureCollection")
                self._send_bytes(payload, "application/geo+json; charset=utf-8", source)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, HTTPError, URLError, ValueError) as exc:
                self._send_error_json(404, f"Could not load dataset: {exc}")
            return

        if parsed.path in ("/", "/index.html"):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        self._send_error_json(405, "This local editor is read-only. Export files from the browser.")

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}", file=sys.stderr)


def main() -> None:
    host = "127.0.0.1"
    port = int(os.environ.get("GNSS_ATLAS_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"GNSS Drift Atlas editor: http://{host}:{port}")
    print(f"Data source: {OWNER}/{REPO}@{BRANCH} (local checkout is fallback)")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping editor...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
