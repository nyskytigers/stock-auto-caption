import hashlib
import ast
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from stock_metadata import Metadata, export_csv
from stock_metadata.core import safe_filename
from stock_metadata.uploads import sync_uploads

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/stock-metadata-assistant/scripts/export_csv.py"


class ReleaseTests(unittest.TestCase):
    def test_metadata_types_and_release_paths(self):
        base = dict(filename="cup.jpg", caption="White cup", keywords=["cup"])
        for change in ({"categories": "Objects"}, {"categories": [["Objects"]]},
                       {"country": None}, {"releases": None}, {"category": True},
                       {"releases": "../release.jpg"}, {"releases": "release.pdf"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                export_csv([Metadata(**dict(base, **change))], "adobe")

    def test_portable_names_and_formula_bom(self):
        for name in ("CON.jpg", "lpt1.png", "NUL", "safe\u202egpj.png"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_filename(name)
        with self.assertRaisesRegex(ValueError, "formula"):
            export_csv([Metadata("cup.jpg", "\ufeff=SUM(1)", ["cup"])], "adobe")
        with self.assertRaisesRegex(ValueError, "control"):
            export_csv([Metadata("cup.jpg", "White\x00cup", ["cup"])], "adobe")

    def test_changed_upload_invalidates_old_metadata(self):
        file = SimpleNamespace(name="cup.JPG", getvalue=lambda: b"original")
        state = {}
        sync_uploads([file], state)
        state["ad_caption_cup.JPG"] = "Reviewed original"
        sync_uploads([file], state)
        self.assertIn("ad_caption_cup.JPG", state)
        file.getvalue = lambda: b"different image"
        sync_uploads([file], state)
        self.assertNotIn("ad_caption_cup.JPG", state)

    def test_duplicate_uploads_fail_before_state_mutation(self):
        state = {"ad_caption_cup.JPG": "keep"}
        files = [SimpleNamespace(name=name, getvalue=lambda: b"x") for name in ("cup.JPG", "CUP.jpg")]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            sync_uploads(files, state)
        self.assertEqual(state, {"ad_caption_cup.JPG": "keep"})

    def test_standalone_adversarial_rows_in_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            script = directory / "temp_script.py"
            script.write_bytes(SCRIPT.read_bytes())
            base = dict(filename="cup.jpg", caption="White cup", keywords=["cup"])
            rows = [[], [None], [dict(base, filename="../cup.jpg")],
                    [dict(base, caption="=HYPERLINK(1)")], [dict(base, releases=None)],
                    [base, dict(base)], [dict(base, categories="Objects")]]
            for i, data in enumerate(rows):
                source, output = directory / "data.json", directory / f"out{i}.csv"
                source.write_text(json.dumps(data), encoding="utf-8")
                run = subprocess.run([sys.executable, "-I", str(script), "--input", str(source), "--marketplace", "adobe", "--output", str(output)], cwd=directory, capture_output=True, text=True)
                with self.subTest(data=data):
                    self.assertEqual(run.returncode, 2, run.stderr)
                    self.assertNotIn("Traceback", run.stderr)
                    self.assertFalse(output.exists())

    def test_generated_script_matches_source(self):
        from tools.build_skill_script import contents
        self.assertEqual(SCRIPT.read_text(encoding="utf-8"), contents())

    def test_literal_platform_headers_and_demo(self):
        import csv
        expected = {
            "adobe": ["Filename", "Title", "Keywords", "Category", "Releases"],
            "shutterstock": ["Filename", "Description", "Keywords", "Categories", "Illustration", "Mature Content", "Editorial"],
            "istock": ["file name", "description", "country", "title", "keywords", "color"],
        }
        data = json.loads((ROOT / "docs/demo/reviewed.json").read_text())
        for site, header in expected.items():
            payload = export_csv([Metadata(**row) for row in data], site)
            self.assertEqual(next(csv.reader(io.StringIO(payload.decode()))), header)
            if site != "istock":
                self.assertEqual((ROOT / f"docs/demo/{site}.csv").read_bytes(), payload)

    def test_standalone_has_no_network_shell_or_dynamic_code(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        allowed = {"dataclasses", "re", "unicodedata", "pathlib", "csv", "io", "argparse", "json", "sys"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(n.name in allowed for n in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertIn(node.module, allowed)
                self.assertEqual(node.level, 0)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, {"eval", "exec", "compile", "__import__"})

    def test_duplicate_json_keys_fail(self):
        from stock_metadata.core import unique_json_object
        with self.assertRaisesRegex(ValueError, "duplicate JSON"):
            json.loads('{"cup.jpg": {}, "cup.jpg": {}}', object_pairs_hook=unique_json_object)

    def test_reproducible_zip(self):
        from tools.package_skill import main
        main()
        path = ROOT / "dist/stock-metadata-assistant.zip"
        first = path.read_bytes()
        main()
        self.assertEqual(path.read_bytes(), first)
        manifest = json.loads(path.with_suffix(".manifest.json").read_text())
        self.assertEqual(manifest["sha256"], hashlib.sha256(first).hexdigest())

    def test_optional_backend_offline_arguments(self):
        from stock_metadata.backends import LocalBackend
        model = MagicMock()
        processor = MagicMock()
        keyword = MagicMock()
        sentence = MagicMock()
        modules = {"transformers": SimpleNamespace(BlipProcessor=processor, BlipForConditionalGeneration=model),
                   "keybert": SimpleNamespace(KeyBERT=keyword),
                   "sentence_transformers": SimpleNamespace(SentenceTransformer=sentence)}
        with patch.dict(sys.modules, modules):
            LocalBackend(local_files_only=True)
        self.assertTrue(model.from_pretrained.call_args.kwargs["local_files_only"])
        self.assertFalse(processor.from_pretrained.call_args.kwargs["use_fast"])
        self.assertTrue(sentence.call_args.kwargs["local_files_only"])

    def test_zip_no_credentials_or_binary_members(self):
        import zipfile
        from tools.package_skill import main
        main()
        with zipfile.ZipFile(ROOT / "dist/stock-metadata-assistant.zip") as archive:
            for member in archive.infolist():
                self.assertFalse(member.filename.startswith(("/", "\\")))
                self.assertNotIn("..", Path(member.filename).parts)
                self.assertNotIn(".env", member.filename)
                archive.read(member).decode("utf-8")
                self.assertEqual(member.external_attr >> 16, 0o100644)
