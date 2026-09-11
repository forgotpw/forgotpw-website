"""Exercise content versions using real files, including a changed asset release."""

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import prepare_site as preparation


class SiteCacheTests(unittest.TestCase):
    def test_changed_asset_gets_a_new_url_without_changing_other_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            shutil.copytree(preparation.SOURCE, source)
            before = {p.relative_to(source): p.read_bytes() for p in source.rglob("*")
                      if p.is_file()}
            # Only redirect the source path; all preparation uses actual filesystem I/O.
            with patch.object(preparation, "SOURCE", source):
                first = preparation.asset_versions(source)
                preparation.prepare_site("prod", root / "first")
                for original, versioned in first.items():
                    self.assertEqual((root / "first" / versioned).read_bytes(),
                                     before[Path(original)])
                    for page in ("index.html", "privacy.html"):
                        text = (root / "first" / page).read_text()
                        self.assertNotIn(original + '"', text)
                self.assertEqual(before, {p.relative_to(source): p.read_bytes()
                                          for p in source.rglob("*") if p.is_file()})
                stylesheet = source / "css/rosa.css"
                stylesheet.write_text(stylesheet.read_text() + "\n/* changed release */\n")
                second = preparation.asset_versions(source)
                preparation.prepare_site("prod", root / "second")
                self.assertNotEqual(first["css/rosa.css"], second["css/rosa.css"])
                self.assertEqual({k: v for k, v in first.items() if k != "css/rosa.css"},
                                 {k: v for k, v in second.items() if k != "css/rosa.css"})
                html = (root / "second/index.html").read_text()
                self.assertIn(second["css/rosa.css"], html)
                self.assertNotIn(first["css/rosa.css"], html)
                self.assertEqual((root / "first" / first["css/rosa.css"]).read_bytes(),
                                 before[Path("css/rosa.css")])


if __name__ == "__main__":
    unittest.main()
