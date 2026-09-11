import gzip
import importlib.util
import json
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "summarize_traffic.py"
SPEC = importlib.util.spec_from_file_location("summarize_traffic", MODULE_PATH)
summarize_traffic = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(summarize_traffic)


def record(**overrides):
    base = {
        "date": "2026-09-10",
        "time": "12:00:00",
        "cs-method": "GET",
        "cs-uri-stem": "/",
        "sc-status": "200",
        "sc-content-type": "text/html",
        "cs(Referer)": "https://www.linkedin.com/feed/?tracking=removed",
        "cs(User-Agent)": "Mozilla/5.0 Safari/605.1.15",
        "c-country": "US",
    }
    base.update(overrides)
    return base


class ParseLogPayloadTests(unittest.TestCase):
    def test_parses_gzipped_newline_delimited_json(self):
        payload = gzip.compress(
            b"\n".join(json.dumps(item).encode() for item in [record(), record(**{"sc-status": "404"})])
        )

        parsed = summarize_traffic.parse_log_payload(payload)

        self.assertEqual(2, len(parsed))
        self.assertEqual("404", parsed[1]["sc-status"])


class SummarizeTests(unittest.TestCase):
    def test_separates_browser_page_views_from_assets_and_bots(self):
        records = [
            record(),
            record(**{"cs-uri-stem": "/privacy.html", "cs(Referer)": "-"}),
            record(
                **{
                    "cs-uri-stem": "/Images/rosa-logo.svg",
                    "sc-content-type": "image/svg+xml",
                }
            ),
            record(
                **{
                    "cs-uri-stem": "/api/status",
                    "sc-content-type": "application/json",
                }
            ),
            record(**{"sc-status": "301"}),
            record(**{"cs(User-Agent)": "LinkedInBot/1.0"}),
        ]

        summary = summarize_traffic.summarize(records)

        self.assertEqual(6, summary["requests"])
        self.assertEqual(3, summary["page_views"])
        self.assertEqual(2, summary["browser_page_views"])
        self.assertEqual(1, summary["bot_requests"])
        self.assertEqual(2, summary["referrers"]["www.linkedin.com"])
        self.assertEqual(1, summary["referrers"]["direct / unavailable"])


if __name__ == "__main__":
    unittest.main()
