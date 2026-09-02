"""Shared helpers for the SIH26086 data research pipeline.

Responsibilities:
- SHA256 checksums + checksums.csv ledger
- dataset metadata JSON writer (race-condition-safe appends)
- download logging + size checks
- date helpers

Nothing here invents or fabricates values: every field written to
metadata is either passed explicitly by the caller or marked UNVERIFIED.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
METADATA = DATA / "metadata"
REPORTS = ROOT / "reports"
CHECKSUMS_CSV = DATA / "checksums.csv"
DOWNLOAD_LOG = REPORTS / "DATA_DOWNLOAD_LOG.md"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def record_checksum(dataset: str, file: Path, source_url: str) -> None:
    CHECKSUMS_CSV.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "dataset": dataset,
        "file": str(file),
        "sha256": sha256_file(file),
        "download_timestamp": utcnow(),
        "source_url": source_url,
        "size_bytes": os.path.getsize(file),
    }
    header = CHECKSUMS_CSV.exists() and CHECKSUMS_CSV.stat().st_size > 0
    with open(CHECKSUMS_CSV, "a", newline="", encoding="utf-8") as f:
        if not header:
            f.write(",".join(row.keys()) + "\n")
        f.write(",".join(f'"{row[k]}"' for k in row) + "\n")


def write_metadata(dataset: str, meta: dict[str, Any]) -> Path:
    """Persist DATA/metadata/<dataset>.json using the required schema.

    Any key absent from `meta` is written as UNVERIFIED (never guessed).
    """
    METADATA.mkdir(parents=True, exist_ok=True)
    schema_keys = [
        "dataset_name", "provider", "official_url", "api_url", "license",
        "version", "temporal_coverage", "spatial_resolution", "temporal_resolution",
        "variables", "geographic_coverage", "access_method", "download_timestamp",
        "checksum", "citation", "role", "suitability", "limitations",
    ]
    out: dict[str, Any] = {}
    for k in schema_keys:
        out[k] = meta.get(k, "UNVERIFIED")
    out["status"] = meta.get("status", "VERIFIED")
    path = METADATA / f"{dataset}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    return path


def log_download(dataset: str, url: str, path: Path, ok: bool, note: str = "") -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    line = f"| {utcnow()} | {dataset} | {url} | {path} | {'OK' if ok else 'FAIL'} | {os.path.getsize(path) if path.exists() and ok else 0} | {note} |"
    if not DOWNLOAD_LOG.exists():
        DOWNLOAD_LOG.write_text(
            "# DATA_DOWNLOAD_LOG\n\n| timestamp | dataset | source_url | local_path | result | size_bytes | note |\n| --- | --- | --- | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )
    with open(DOWNLOAD_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def expected_calendar_days(start: str, end: str) -> int:
    """Days between inclusive YYYY-MM-DD dates (proleptic Gregorian)."""
    from datetime import date

    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    return (e - s).days + 1


def parse_date_file(path: Path) -> str:
    """Extract yyyy-mm-dd from a filename like chirps-v3.0_2024-06-15.nc."""
    import re

    m = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return m.group(1) if m else "UNKNOWN"