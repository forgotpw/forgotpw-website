"""Check the actual deployment artifacts and their crawlable page relationships."""

from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from scripts.prepare_site import SOURCE, asset_versions, prepare_site


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class SiteSEOTests(unittest.TestCase):
    def test_real_release_artifacts(self):
        source_html = {p: p.read_bytes() for p in SOURCE.rglob("*.html")}
        with tempfile.TemporaryDirectory() as temporary:
            for environment in ("dev", "prod"):
                site = Path(temporary) / environment
                prepare_site(environment, site)
                pages = {}
                for source, original in source_html.items():
                    page = site / source.relative_to(SOURCE)
                    text = page.read_text(encoding="utf-8")
                    pages[page.name] = Page(text)
                    robots = [a["content"] for t, a in pages[page.name].elements
                              if t == "meta" and a.get("name") == "robots"]
                    self.assertEqual(robots, ["noindex, follow" if environment == "dev"
                                              else "index, follow"])
                    if environment == "prod":
                        normalized = text
                        for asset, versioned in asset_versions(SOURCE).items():
                            normalized = normalized.replace(versioned, asset)
                        self.assertEqual(normalized.encode(), original)
                for name, page in pages.items():
                    canonical = [a["href"] for t, a in page.elements
                                 if t == "link" and a.get("rel") == "canonical"]
                    self.assertEqual(canonical, ["https://www.rosa.bot/" +
                                                 ("" if name == "index.html" else name)])
                    self.assertEqual(sum(t == "h1" for t, _ in page.elements), 1)
                    for tag, attrs in page.elements:
                        if tag == "img":
                            self.assertIn("alt", attrs)
                            self.assertIn("width", attrs)
                            self.assertIn("height", attrs)
                        # Check every local page, asset, and fragment reference.
                        reference = attrs.get("href", attrs.get("src", ""))
                        url = urlsplit(reference)
                        if url.scheme or url.netloc or not reference:
                            continue
                        target = (url.path.lstrip("/") or
                                  ("index.html" if reference.startswith("/") else name))
                        self.assertTrue((site / target).is_file(), reference)
                        if url.fragment:
                            ids = {a.get("id") for _, a in pages[target].elements}
                            self.assertIn(url.fragment, ids, reference)
                sitemap = ET.parse(site / "sitemap.xml")
                urls = [e.text for e in sitemap.findall(".//{*}loc")]
                self.assertEqual(urls, ["https://www.rosa.bot/",
                                        "https://www.rosa.bot/privacy.html"])
                robots = (site / "robots.txt").read_text()
                self.assertIn("Allow: /", robots)
                self.assertNotIn("Disallow:", robots)
                self.assertIn("Sitemap: https://www.rosa.bot/sitemap.xml", robots)
                html = (site / "index.html").read_text()
                schema = json.loads(html.split('<script type="application/ld+json">')[1]
                                    .split("</script>")[0])
                self.assertEqual(schema["@type"], "WebSite")
                self.assertEqual(schema["name"], "Rosa")
                self.assertEqual(schema["url"], urls[0])
                for resource in ("scripts/rosa.js", "Images/rosa-social-card.png",
                                 "videos/rosa-explainer-v1.mp4", "rosa.vcf"):
                    self.assertEqual((site / resource).read_bytes(),
                                     (SOURCE / resource).read_bytes())
        self.assertEqual(source_html, {p: p.read_bytes() for p in source_html})

    def test_invalid_environment_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "site"
            with self.assertRaises(ValueError):
                prepare_site("staging", output)
            self.assertFalse(output.exists())

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            sentinel = output / "keep.txt"
            sentinel.write_text("Existing work")
            with self.assertRaises(FileExistsError):
                prepare_site("prod", output)
            self.assertEqual(sentinel.read_text(), "Existing work")


if __name__ == "__main__":
    unittest.main()
