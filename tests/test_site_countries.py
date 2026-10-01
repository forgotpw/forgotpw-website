"""Where Rosa works: the homepage says US and Canadian numbers where a visitor starts, and the policies name both countries wherever they say who may use Rosa."""

from pathlib import Path
import re
import unittest

from scripts.prepare_site import SOURCE


def sentences(page):
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", (SOURCE / page).read_text()))
    return [s.strip() for s in re.split(r"(?<=[.!?])\s", text)]


class CountryTests(unittest.TestCase):
    def test_homepage_says_us_and_canada_where_visitors_start(self):
        text = re.sub(r"\s+", " ", (SOURCE / "index.html").read_text())
        hero_note = re.search(r'<p class="cta-note">(.*?)</p>', text).group(1)
        self.assertIn("from a US or Canadian mobile number", hero_note)
        closing = text[text.index('class="closing"'):]
        self.assertIn("US and Canadian mobile numbers for now.", closing)

    def test_policies_name_both_countries_for_who_may_use_rosa(self):
        for page in ("terms.html", "privacy.html"):
            who = [s for s in sentences(page) if re.search(r"Rosa is (offered|meant for)", s)]
            self.assertTrue(who, page)
            for sentence in who:
                self.assertIn("United States and Canada", sentence, f"{page}: {sentence}")


if __name__ == "__main__":
    unittest.main()
