import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from stock_metadata import export_csv, Metadata

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "stock-metadata-assistant"


class SkillTests(unittest.TestCase):
    def test_independent_script_parity(self):
        record = dict(filename="mug.jpg", caption="White mug", keywords=["mug", "white", "ceramic", "oak", "table", "light", "drinkware"], categories=["Objects"], category=4)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / "standalone.py"
            script.write_bytes((SKILL / "scripts/export_csv.py").read_bytes())
            source = root / "data.json"
            source.write_text(json.dumps([record]), encoding="utf-8")
            for site in ("adobe", "shutterstock", "istock"):
                target = root / f"{site}.csv"
                result = subprocess.run([sys.executable, str(script), "--input", str(source), "--marketplace", site, "--output", str(target)], cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(target.read_bytes(), export_csv([Metadata(**record)], site))

    def test_script_invalid_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, output = root / "input.json", root / "output.csv"
            source.write_text('[{"filename":"../bad.jpg","caption":"test","keywords":["test"]}]')
            command = [sys.executable, str(SKILL / "scripts/export_csv.py"), "--input", str(source), "--marketplace", "adobe", "--output", str(output)]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertFalse(output.exists())
            output.write_text("keep")
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
            self.assertEqual(output.read_text(), "keep")

    def test_zip_allowlist(self):
        from tools.package_skill import main, FILES
        main()
        with zipfile.ZipFile(ROOT / "dist/stock-metadata-assistant.zip") as archive:
            self.assertEqual(set(archive.namelist()), {"stock-metadata-assistant/" + f for f in FILES})
            for name in archive.namelist():
                archive.read(name).decode("utf-8")
            self.assertLess(len(archive.read("stock-metadata-assistant/scripts/export_csv.py")), 20_000)

    def test_frontmatter_and_references(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: stock-metadata-assistant\n"))
        self.assertIn("description:", text.split("---")[1])
        self.assertEqual((SKILL / "references/platform-rules.md").read_bytes(), (ROOT / "docs/platform-rules.md").read_bytes())
