#!/usr/bin/env python3
"""Download the public CMS Exchange PUF inputs used by this project.

CMS publishes these data as stable ZIP downloads rather than through an API.
The script preserves the ZIPs, skips valid existing downloads, retries transient
failures, validates every archive, and writes a SHA-256 manifest.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
import shutil
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_ROOT = ROOT / "data" / "raw" / "cms_downloads"
BASE = "https://download.cms.gov/marketplace-puf/{year}/{filename}"

DATASETS = {
    "01_transparency_pufs": (range(2017, 2027), "transparency-in-coverage-puf.zip"),
    "02_rate_pufs": (range(2015, 2027), "rate-puf.zip"),
    "03_plan_attributes_pufs": (range(2015, 2027), "plan-attributes-puf.zip"),
    "04_service_area_pufs": (range(2015, 2027), "service-area-puf.zip"),
    "05_plan_crosswalks": (range(2017, 2027), "plan-id-crosswalk-puf.zip"),
}

DOCUMENTS = {
    "exchange-pufs-general-information-py26.pdf": "https://www.cms.gov/files/document/exchange-pufs-geninfofacts-py26.pdf-0",
    "exchange-pufs-faq-py26.pdf": "https://www.cms.gov/files/document/exchange-pufs-faqs-py26.pdf-0",
    "exchange-pufs-user-agreement-py26.pdf": "https://www.cms.gov/files/document/exchange-pufs-disclaimagree-py26.pdf-0",
    "transparency-disclaimer-py26.pdf": "https://www.cms.gov/files/document/transparency-coverage-datadisclaimer-py26.pdf-0",
    "transparency-data-dictionary-py26.pdf": "https://www.cms.gov/files/document/transparency-coverage-puf-datadictionary-py26.pdf",
    "rate-data-dictionary-py26.pdf": "https://www.cms.gov/files/document/rate-datadictionary-py26.pdf",
    "plan-attributes-data-dictionary-py26.pdf": "https://www.cms.gov/files/document/planattributes-datadictionary-py26.pdf",
    "service-area-data-dictionary-py26.pdf": "https://www.cms.gov/files/document/servicearea-datadictionary-py26.pdf",
    "plan-crosswalk-data-dictionary-py26.pdf": "https://www.cms.gov/files/document/plan-id-crosswalk-datadictionary-py26.pdf",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_file(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return False
    if path.suffix.lower() == ".zip":
        try:
            with zipfile.ZipFile(path) as archive:
                return archive.testzip() is None
        except zipfile.BadZipFile:
            return False
    if path.suffix.lower() == ".pdf":
        return path.read_bytes()[:5] == b"%PDF-"
    return True


def download(url: str, destination: Path, force: bool, dry_run: bool) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and valid_file(destination) and not force:
        print(f"SKIP  {destination.relative_to(ROOT)}")
        return "existing"
    if dry_run:
        print(f"WOULD DOWNLOAD  {url} -> {destination.relative_to(ROOT)}")
        return "dry_run"

    partial = destination.with_suffix(destination.suffix + ".part")
    request = Request(url, headers={"User-Agent": "insured-but-unprotected-research/0.1"})
    last_error = None
    for attempt in range(1, 4):
        try:
            print(f"GET   {url}")
            with urlopen(request, timeout=120) as response, partial.open("wb") as output:
                shutil.copyfileobj(response, output, length=1024 * 1024)
            partial.replace(destination)
            if not valid_file(destination):
                raise ValueError(f"Downloaded file failed validation: {destination}")
            return "downloaded"
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            last_error = error
            partial.unlink(missing_ok=True)
            if attempt < 3:
                time.sleep(2**attempt)
    raise RuntimeError(f"Failed after 3 attempts: {url}") from last_error


def targets():
    for folder, (years, filename) in DATASETS.items():
        for year in years:
            output_name = f"{year}_{filename}"
            yield BASE.format(year=year, filename=filename), DOWNLOAD_ROOT / folder / output_name
    for output_name, url in DOCUMENTS.items():
        yield url, DOWNLOAD_ROOT / "06_documentation" / output_name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Replace valid existing downloads")
    parser.add_argument("--dry-run", action="store_true", help="Print downloads without fetching")
    args = parser.parse_args()

    records = []
    for url, destination in targets():
        status = download(url, destination, args.force, args.dry_run)
        records.append({
            "relative_path": str(destination.relative_to(ROOT)),
            "source_url": url,
            "status": status,
            "bytes": destination.stat().st_size if destination.exists() else "",
            "sha256": sha256(destination) if destination.exists() and valid_file(destination) else "",
        })

    if not args.dry_run:
        manifest = DOWNLOAD_ROOT / "download_manifest.csv"
        with manifest.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)
        print(f"\nComplete. Manifest: {manifest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
