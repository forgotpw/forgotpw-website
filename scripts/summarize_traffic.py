#!/usr/bin/env python3
"""Summarize privacy-minimized Rosa CloudFront access logs from S3."""

from __future__ import annotations

import argparse
import gzip
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse


ENVIRONMENTS = {
    "dev": {
        "account_id": "478543871670",
        "bucket": "rosa-website-traffic-logs-dev-478543871670",
    },
    "prod": {
        "account_id": "162109821699",
        "bucket": "rosa-website-traffic-logs-prod-162109821699",
    },
}

BOT_PATTERN = re.compile(
    r"bot|crawler|spider|slurp|facebookexternalhit|linkedinbot|twitterbot|"
    r"whatsapp|preview|uptime|monitor|headless",
    re.IGNORECASE,
)


def aws_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["aws", *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def aws_json(*arguments: str) -> dict:
    return json.loads(aws_bytes(*arguments, "--output", "json"))


def parse_log_payload(payload: bytes) -> list[dict]:
    if payload.startswith(b"\x1f\x8b"):
        payload = gzip.decompress(payload)

    text = payload.decode("utf-8")
    stripped = text.strip()
    if not stripped:
        return []

    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            records = parsed.get("Records")
            return records if isinstance(records, list) else [parsed]

    records = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON log record on line {line_number}") from error
        if not isinstance(record, dict):
            raise ValueError(f"Log record on line {line_number} is not an object")
        records.append(record)
    return records


def record_timestamp(record: dict) -> datetime:
    return datetime.fromisoformat(f"{record['date']}T{record['time']}+00:00")


def is_page_request(record: dict) -> bool:
    if record.get("cs-method") != "GET":
        return False
    try:
        status = int(record.get("sc-status", 0))
    except (TypeError, ValueError):
        return False
    if status < 200 or status >= 300:
        return False

    content_type = str(record.get("sc-content-type", "")).lower()
    return content_type.startswith("text/html")


def is_bot(record: dict) -> bool:
    return bool(BOT_PATTERN.search(str(record.get("cs(User-Agent)", ""))))


def referrer_source(record: dict) -> str:
    value = str(record.get("cs(Referer)", "-")).strip()
    if not value or value == "-":
        return "direct / unavailable"
    parsed = urlparse(value)
    return parsed.hostname or value.split("?", 1)[0]


def summarize(records: list[dict]) -> dict:
    result = {
        "requests": len(records),
        "page_views": 0,
        "browser_page_views": 0,
        "bot_requests": 0,
        "statuses": Counter(),
        "page_paths": Counter(),
        "referrers": Counter(),
        "user_agents": Counter(),
        "countries": Counter(),
        "daily": defaultdict(lambda: Counter(requests=0, browser_page_views=0)),
    }

    for record in records:
        day = str(record.get("date", "unknown"))
        result["daily"][day]["requests"] += 1
        result["statuses"][str(record.get("sc-status", "unknown"))] += 1
        result["user_agents"][str(record.get("cs(User-Agent)", "unknown"))] += 1
        result["countries"][str(record.get("c-country", "unknown"))] += 1

        bot = is_bot(record)
        page_request = is_page_request(record)
        if bot:
            result["bot_requests"] += 1
        if page_request:
            result["page_views"] += 1
            result["page_paths"][str(record.get("cs-uri-stem", "unknown"))] += 1
            result["referrers"][referrer_source(record)] += 1
            if not bot:
                result["browser_page_views"] += 1
                result["daily"][day]["browser_page_views"] += 1

    return result


def print_counter(title: str, counter: Counter, limit: int = 10) -> None:
    print(f"\n{title}")
    if not counter:
        print("  (none)")
        return
    for value, count in counter.most_common(limit):
        normalized = value if len(value) <= 120 else f"{value[:117]}..."
        print(f"  {count:>7}  {normalized}")


def print_summary(summary: dict, environment: str, days: int) -> None:
    print(f"Rosa traffic summary: {environment}, last {days} day(s)")
    print(f"Requests:                    {summary['requests']}")
    print(f"Successful page requests:    {summary['page_views']}")
    print(f"Approx. browser page views:  {summary['browser_page_views']}")
    print(f"Bot-like requests:           {summary['bot_requests']}")
    print("\nDaily trend")
    for day in sorted(summary["daily"]):
        counts = summary["daily"][day]
        print(
            f"  {day}  requests={counts['requests']}  "
            f"browser_page_views={counts['browser_page_views']}"
        )
    print_counter("Top page paths", summary["page_paths"])
    print_counter("Referrer sources", summary["referrers"])
    print_counter("Status codes", summary["statuses"])
    print_counter("Countries", summary["countries"])
    print_counter("User agents", summary["user_agents"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", choices=ENVIRONMENTS, required=True)
    parser.add_argument("--days", type=int, default=7)
    arguments = parser.parse_args()
    if arguments.days < 1:
        parser.error("--days must be at least 1")

    environment = ENVIRONMENTS[arguments.env]
    identity = aws_json("sts", "get-caller-identity")
    if identity.get("Account") != environment["account_id"]:
        raise RuntimeError(
            f"Wrong AWS account: expected {environment['account_id']}, "
            f"got {identity.get('Account')}"
        )

    cutoff = datetime.now(timezone.utc) - timedelta(days=arguments.days)
    listing = aws_json(
        "s3api",
        "list-objects-v2",
        "--bucket",
        environment["bucket"],
    )
    objects = [
        item
        for item in listing.get("Contents", [])
        if datetime.fromisoformat(item["LastModified"]) >= cutoff
    ]

    records = []
    for item in objects:
        key = item["Key"]
        try:
            payload = aws_bytes(
                "s3",
                "cp",
                f"s3://{environment['bucket']}/{key}",
                "-",
                "--only-show-errors",
            )
            records.extend(
                record for record in parse_log_payload(payload) if record_timestamp(record) >= cutoff
            )
        except Exception as error:
            raise RuntimeError(f"Could not read access log object {key}") from error

    print_summary(summarize(records), arguments.env, arguments.days)
    if not objects:
        print("\nNo delivered log objects were found in this period.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        sys.stderr.write(error.stderr.decode("utf-8", errors="replace"))
        raise SystemExit(error.returncode) from error
