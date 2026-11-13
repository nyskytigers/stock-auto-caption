import csv
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch, MagicMock
import zipfile


@unittest.skipUnless(importlib.util.find_spec("streamlit") and importlib.util.find_spec("PIL"), "UI extras not installed")
class UITests(unittest.TestCase):
    def test_empty_app_no_model_load(self):
        from streamlit.testing.v1 import AppTest
        root = Path(__file__).resolve().parents[1]
        app = AppTest.from_file(str(root / "app.py")).run(timeout=20)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, "StockWords AI")

    def test_three_export_adapters_use_edited_state(self):
        import exporters
        for cls, config in ((exporters.ShutterstockExporter, {"categories": ["Objects"]}),
                            (exporters.AdobeStockExporter, {"category_id": 4}),
                            (exporters.IStockExporter, {})):
            exporter = cls()
            file = SimpleNamespace(name="Mug.JPG")
            state = {f"{exporter.key_prefix}caption_Mug.JPG": "Edited White Mug",
                     f"{exporter.key_prefix}keywords_Mug.JPG": "mug, white, ceramic, table, oak, light, drinkware"}
            with self.subTest(cls=cls.__name__), patch.object(exporters.st, "session_state", state), patch.object(exporters.st, "download_button") as download:
                exporter.draw_export_button([file], config)
                payload = download.call_args.args[1]
                if isinstance(exporter, exporters.IStockExporter):
                    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                        payload = archive.read("Mug.JPG.csv")
                row = list(csv.reader(io.StringIO(payload.decode())))[1]
                self.assertEqual(row[:2], ["Mug.JPG", "Edited White Mug"])

    def test_invalid_metadata_blocks_download(self):
        import exporters
        exporter = exporters.AdobeStockExporter()
        with patch.object(exporters.st, "session_state", {}), patch.object(exporters.st, "download_button") as download, patch.object(exporters.st, "error") as error:
            exporter.draw_export_button([SimpleNamespace(name="Mug.JPG")], {})
            download.assert_not_called()
            error.assert_called_once()

    def test_corrupt_upload_does_not_block_next_editor(self):
        from PIL import Image
        import exporters
        broken = io.BytesIO(b"not an image")
        broken.name = "bad.jpg"
        valid = io.BytesIO()
        Image.new("RGB", (300, 300)).save(valid, format="PNG")
        valid.name = "good.png"
        backend = MagicMock()
        backend.generate_caption.return_value = "White mug"
        backend.refine_caption_and_keywords.return_value = ("White mug", "white, mug")
        # The actual PIL decode and processing execute, only Streamlit rendering is mocked.
        state = {}
        for cls in (exporters.ShutterstockExporter, exporters.AdobeStockExporter, exporters.IStockExporter):
            ui = MagicMock()
            ui.session_state = state
            ui.columns.return_value = [MagicMock(), MagicMock()]
            with self.subTest(cls=cls.__name__), patch.object(exporters, "st", ui):
                exporter = cls()
                exporter.draw_image_editors([broken, valid], {}, backend)
                self.assertEqual(state[f"{exporter.key_prefix}caption_good.png"], "White mug")
                ui.error.assert_called_once()

    def test_batch_append_deduplicates_keywords(self):
        import exporters
        exporter = exporters.AdobeStockExporter()
        state = {"ad_caption_mug.jpg": "White mug", "ad_keywords_mug.jpg": "Mug, White"}
        ui = MagicMock()
        ui.session_state = state
        ui.text_area.side_effect = ["on a table", "mug, table"]
        ui.columns.return_value = [MagicMock(), MagicMock()]
        ui.button.return_value = True
        with patch.object(exporters, "st", ui):
            exporter.draw_batch_controls([SimpleNamespace(name="mug.jpg")])
        self.assertEqual(state["ad_caption_mug.jpg"], "White mug on a table")
        self.assertEqual(state["ad_keywords_mug.jpg"], "Mug, White, table")
