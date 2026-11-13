import csv
import io
import unittest
import zipfile
from stock_metadata import Metadata, clean_caption, clean_keywords, export_csv, export_istock_zip
from stock_metadata.core import refine_caption, safe_filename
from stock_metadata.csv_export import SCHEMAS


def sample(**kwargs):
    values = dict(filename="Coffee.JPG", caption="NYC coffee mug on an oak table",
                  keywords=["coffee", "mug", "white", "ceramic", "oak", "table", "window light"],
                  categories=["Food and drink"], category=4)
    values.update(kwargs)
    return Metadata(**values)


class CoreTests(unittest.TestCase):
    def test_caption_case_and_whitespace(self):
        self.assertEqual(clean_caption("  NYC\n  and NASA  "), "NYC and NASA")

    def test_no_silent_truncation(self):
        self.assertEqual(len(clean_caption("x" * 300)), 300)

    def test_keyword_order_and_case(self):
        self.assertEqual(clean_keywords("Cat, cat,  coffee mug , ,CAT,dog"), ["Cat", "coffee mug", "dog"])

    def test_invalid_keywords(self):
        for value in (None, 1, ["a,b"], [1]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                clean_keywords(value)

    def test_refine_does_not_change_names(self):
        class Fake:
            def extract_keywords(self, caption, **options):
                return [("NYC", .9), ("nyc", .8), ("coffee mug", .7)]
        self.assertEqual(refine_caption("NYC and NASA", Fake()), ("NYC and NASA", "NYC, coffee mug"))

    def test_filename_exact(self):
        for name in ("Cat.v2.JPG", "한국 사진.png", "coffee mug.jpeg"):
            self.assertEqual(safe_filename(name), name)

    def test_filename_traversal(self):
        for name in ("../a.jpg", "..\\a.jpg", "C:a.jpg", "a\x00.jpg", "*", ".", "", "a.jpg "):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_filename(name)

    def test_schema_and_roundtrip(self):
        for site in SCHEMAS:
            with self.subTest(site=site):
                rows = list(csv.reader(io.StringIO(export_csv([sample()], site).decode())))
                self.assertEqual(rows[0], SCHEMAS[site])
                self.assertEqual(rows[1][0], "Coffee.JPG")
                self.assertEqual(len(rows[1]), len(rows[0]))

    def test_quoted_csv(self):
        data = export_csv([sample(caption='A mug, labeled "coffee"')], "shutterstock")
        row = list(csv.reader(io.StringIO(data.decode())))[1]
        self.assertEqual(row[1], 'A mug, labeled "coffee"')

    def test_shutterstock_flags(self):
        row = list(csv.reader(io.StringIO(export_csv([sample(editorial="yes", mature="no", illustration="yes")], "shutterstock").decode())))[1]
        self.assertEqual(row[-3:], ["Yes", "No", "Yes"])

    def test_shutterstock_boundaries(self):
        export_csv([sample(caption="a" * 2048, keywords=[str(i) for i in range(50)])], "shutterstock")
        for options in (dict(caption="a" * 2049), dict(keywords=["one"]), dict(keywords=[str(i) for i in range(51)]), dict(categories=[]), dict(categories=["fake"]), dict(editorial="maybe")):
            with self.subTest(options=options), self.assertRaises(ValueError):
                export_csv([sample(**options)], "shutterstock")

    def test_adobe_boundaries(self):
        export_csv([sample(filename="x" * 26 + ".jpg", caption="x" * 70, keywords=[str(i) for i in range(50)])], "adobe")
        for options in (dict(filename="x" * 27 + ".jpg"), dict(caption="x" * 71), dict(caption="a,b"), dict(category=22), dict(releases="x" * 31)):
            with self.subTest(options=options), self.assertRaises(ValueError):
                export_csv([sample(**options)], "adobe")

    def test_adobe_batch_row_limit(self):
        with self.assertRaisesRegex(ValueError, "5000"):
            export_csv([sample(filename=f"{i}.jpg") for i in range(5001)], "adobe")

    def test_adobe_byte_limit(self):
        records = [sample(filename=f"{i}.jpg", keywords=["longword" * 100]) for i in range(1500)]
        with self.assertRaisesRegex(ValueError, "1 MB"):
            export_csv(records, "adobe")

    def test_duplicates(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            export_csv([sample(), sample(filename="coffee.jpg")], "adobe")

    def test_error_and_formula_cells(self):
        for options in (dict(caption="Error"), dict(keywords="Error"), dict(caption="=1+1"), dict(filename="@image.jpg")):
            with self.subTest(options=options), self.assertRaises(ValueError):
                export_csv([sample(**options)], "adobe")

    def test_zip_no_stem_collision(self):
        payload = export_istock_zip([sample(filename="cat.jpg"), sample(filename="cat.png")])
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            self.assertEqual(archive.namelist(), ["cat.jpg.csv", "cat.png.csv"])
            self.assertIn(b"cat.png", archive.read("cat.png.csv"))

    def test_unknown_site(self):
        with self.assertRaises(ValueError):
            export_csv([], "other")
