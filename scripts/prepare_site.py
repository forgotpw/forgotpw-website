#!/usr/bin/env python3
"""Prepare deployment files, excluding development HTML from search indexing."""

import argparse
from pathlib import Path
import shutil


SOURCE = Path(__file__).resolve().parents[1] / "src"
ROBOTS_TAG = '<meta name="robots" content="index, follow" />'


def prepare_site(environment: str, destination: Path) -> None:
    if environment not in ("dev", "prod"):
        raise ValueError("Environment must be dev or prod")
    # Validate before copying: a new page must explicitly declare its search policy.
    for page in SOURCE.rglob("*.html"):
        if page.read_text(encoding="utf-8").count(ROBOTS_TAG) != 1:
            raise ValueError(f"Expected one production robots tag in {page}")
    # An existing destination is an error, so an old release cannot leak into this one.
    shutil.copytree(SOURCE, destination)
    if environment == "dev":
        for page in destination.rglob("*.html"):
            page.write_text(
                page.read_text(encoding="utf-8").replace(
                    ROBOTS_TAG, '<meta name="robots" content="noindex, follow" />'
                ),
                encoding="utf-8",
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", required=True, choices=("dev", "prod"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    prepare_site(args.environment, args.output)
