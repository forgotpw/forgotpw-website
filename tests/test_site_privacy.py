"""The privacy policy's claims about the save and view pages, and the homepage's Text Rosa links."""

from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

from scripts.prepare_site import SOURCE


class Anchors(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.hrefs = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == "a" and dict(attrs).get("href", "").startswith("sms:"):
            self.hrefs.append(dict(attrs)["href"])


class PrivacyPolicyTests(unittest.TestCase):
    def setUp(self):
        text = (SOURCE / "privacy.html").read_text()
        self.paragraphs = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", p)).strip()
                           for p in re.findall(r"<p>(.*?)</p>", text, re.S)]

    def test_save_and_view_pages_send_nothing_to_third_parties(self):
        paragraph = next(p for p in self.paragraphs if p.startswith("The Rosa pages where you save and view password parts"))
        self.assertIn("send nothing to third parties", paragraph)
        for gone in ("Google Analytics", "Google Fonts", "unpkg"):
            self.assertNotIn(gone, paragraph)
        for gone in ("Google Fonts", "unpkg"):
            self.assertFalse([p for p in self.paragraphs if gone in p], gone)

    def test_homepage_tags_are_still_disclosed(self):
        homepage = next(p for p in self.paragraphs if p.startswith("Our homepage (www.rosa.bot) uses tags from Google"))
        self.assertIn("Google Analytics", homepage)
        self.assertIn("Facebook Pixel", homepage)


class TextRosaLinkTests(unittest.TestCase):
    def test_every_page_links_to_the_same_sms_number(self):
        numbers = set()
        for page in ("index.html", "privacy.html", "terms.html", "security.html"):
            hrefs = Anchors((SOURCE / page).read_text()).hrefs
            numbers.update(hrefs)
        self.assertEqual(numbers, {"sms:+18647778711"})
        self.assertTrue(Anchors((SOURCE / "index.html").read_text()).hrefs)


if __name__ == "__main__":
    unittest.main()
