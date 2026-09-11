#!/usr/bin/env python3
"""Prepare fresh asset URLs and exclude development HTML from search indexing."""

import argparse
import hashlib
from pathlib import Path
import shutil


SOURCE = Path(__file__).resolve().parents[1] / "src"
ROBOTS_TAG = '<meta name="robots" content="index, follow" />'
# These assets have stable source names. Release copies get content-based names;
# original URLs remain available for old pages, shared links and local previews.
VERSIONED_ASSETS = (
    "css/rosa.css", "scripts/rosa.js", "Images/rosa-logo.svg",
    "Images/favicon-32x32.png", "Images/apple-touch-icon.png",
    "Images/rosa-social-card.png", "Images/rosa-explainer-poster.jpg",
    "videos/rosa-explainer-v1.mp4", "videos/rosa-explainer-en.vtt",
)


def asset_versions(source: Path) -> dict[str, str]:
    versions = {}
    for name in VERSIONED_ASSETS:
        path = source / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        versions[name] = str(Path(name).with_name(f"{path.stem}.{digest}{path.suffix}"))
    return versions


def prepare_site(environment: str, destination: Path) -> None:
    if environment not in ("dev", "prod"):
        raise ValueError("Environment must be dev or prod")
    # Validate before copying: a new page must explicitly declare its search policy.
    for page in SOURCE.rglob("*.html"):
        if page.read_text(encoding="utf-8").count(ROBOTS_TAG) != 1:
            raise ValueError(f"Expected one production robots tag in {page}")
    versions = asset_versions(SOURCE)
    # An existing destination is an error, so an old release cannot leak into this one.
    shutil.copytree(SOURCE, destination)
    for original, versioned in versions.items():
        shutil.copyfile(SOURCE / original, destination / versioned)
    for page in destination.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        for original, versioned in versions.items():
            # Matches relative and absolute social-image URLs, leaving canonicals alone.
            text = text.replace(original + '"', versioned + '"')
        if environment == "dev":
            text = text.replace(
                ROBOTS_TAG, '<meta name="robots" content="noindex, follow" />'
            )
        page.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", required=True, choices=("dev", "prod"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare_site(args.environment, args.output)
