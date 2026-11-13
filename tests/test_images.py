import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from stock_metadata import process_image
from stock_metadata.cli import run_batch


@unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow not installed; CI installs images extra")
class ImageTests(unittest.TestCase):
    def test_full_resolution_and_original_unchanged(self):
        from PIL import Image
        class Backend:
            def generate_caption(self, image):
                assert image.size == (600, 400)
                assert image.mode == "RGB"
                return "NYC mug"
            def refine_caption_and_keywords(self, raw, categories):
                return raw, "mug, NYC"
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "image.png"
            Image.new("RGBA", (600, 400)).save(source)
            before = hashlib.sha256(source.read_bytes()).digest()
            record = process_image(source, Backend(), source.name)
            self.assertEqual(record.filename, source.name)
            self.assertEqual(record.caption, "NYC mug")
            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), before)

    def test_corrupt_file_does_not_stop_batch(self):
        from PIL import Image
        class Backend:
            def generate_caption(self, image):
                return "White mug"
            def refine_caption_and_keywords(self, raw, categories):
                return raw, "white, mug"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            Image.new("RGB", (2, 2)).save(root / "good.png")
            (root / "bad.jpg").write_bytes(b"broken")
            rows, errors = run_batch(root, "adobe", backend=Backend())
            self.assertEqual([r.filename for r in rows], ["good.png"])
            self.assertEqual(errors[0]["filename"], "bad.jpg")
