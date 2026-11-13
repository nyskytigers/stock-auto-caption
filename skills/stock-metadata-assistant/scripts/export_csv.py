# MIT License; Copyright (c) 2025 NYskytigers. See bundled LICENSE.
"""Pure metadata normalization and optional read-only image processing."""
from dataclasses import dataclass, field
import re
import unicodedata


def clean_caption(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("caption must be text")
    # Keep proper names, acronyms and meaningful case; never truncate silently.
    return " ".join(unicodedata.normalize("NFC", value).split())


def clean_keywords(value) -> list[str]:
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, (list, tuple)):
        raise ValueError("keywords must be a list or comma-separated text")
    result, seen = [], set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError("each keyword must be text")
        item = clean_caption(item)
        if "," in item:
            raise ValueError("a keyword cannot contain a comma")
        if item and item.casefold() not in seen:
            result.append(item)
            seen.add(item.casefold())
    return result


def safe_filename(value: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        raise ValueError("filename must be a nonempty basename")
    if re.search(r'[\\/:*?"<>|\x00-\x1f\x7f]', value) or value.endswith((" ", ".")):
        raise ValueError(f"unsafe filename: {value!r}; use the exact basename")
    return value


@dataclass
class Metadata:
    filename: str
    caption: str
    keywords: list[str] | str
    categories: list[str] = field(default_factory=list)
    category: str | int = ""
    releases: str = ""
    editorial: str = "no"
    mature: str = "no"
    illustration: str = "no"
    country: str = ""
    color: str = "yes"

    def normalized(self):
        return Metadata(
            filename=safe_filename(self.filename), caption=clean_caption(self.caption),
            keywords=clean_keywords(self.keywords), categories=list(self.categories),
            category=self.category, releases=self.releases, editorial=self.editorial,
            mature=self.mature, illustration=self.illustration, country=self.country,
            color=self.color,
        )


def refine_caption(raw_caption, keyword_model):
    caption = clean_caption(raw_caption)
    keywords = keyword_model.extract_keywords(
        caption, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=25)
    return caption, ", ".join(clean_keywords([term for term, _ in keywords]))


def process_image(source, backend, filename=None) -> Metadata:
    """Decode before inference, close resources, never write to the source."""
    from PIL import Image, ImageOps
    name = safe_filename(filename or source.name)
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        image.load()
    try:
        caption = backend.generate_caption(image)
        caption, keywords = backend.refine_caption_and_keywords(caption, [])
        return Metadata(name, caption, keywords).normalized()
    finally:
        image.close()

"""Verified CSV layouts; no pandas or Streamlit dependency.

Rule provenance and verification date: docs/platform-rules.md.
Validation rejects invalid data instead of changing filenames or truncating fields.
"""
import csv
import io
import zipfile


SCHEMAS = {
    "shutterstock": ["Filename", "Description", "Keywords", "Categories", "Illustration", "Mature Content", "Editorial"],
    "adobe": ["Filename", "Title", "Keywords", "Category", "Releases"],
    "istock": ["file name", "description", "country", "title", "keywords", "color"],
}

SHUTTERSTOCK_CATEGORIES = {
    "Abstract", "Animals/Wildlife", "Arts", "Backgrounds/Textures", "Beauty/Fashion",
    "Buildings/Landmarks", "Business/Finance", "Celebrities", "Education", "Food and drink",
    "Healthcare/Medical", "Holidays", "Industrial", "Interiors", "Miscellaneous", "Nature",
    "Objects", "Parks/Outdoor", "People", "Religion", "Science", "Signs/Symbols",
    "Sports/Recreation", "Technology", "Transportation", "Vintage",
}


def flag(value):
    if not isinstance(value, str) or value.casefold() not in {"yes", "no"}:
        raise ValueError("flags must be yes or no")
    return value.capitalize()


def validate(record: Metadata, marketplace: str) -> Metadata:
    if marketplace not in SCHEMAS:
        raise ValueError(f"unknown marketplace: {marketplace}")
    m = record.normalized()
    if not m.caption or m.caption.casefold() == "error" or not m.keywords or any(k.casefold() == "error" for k in m.keywords):
        raise ValueError(f"{m.filename}: caption and keywords must contain reviewed metadata")
    if marketplace == "shutterstock":
        if len(m.caption) > 2048 or not 7 <= len(m.keywords) <= 50:
            raise ValueError(f"{m.filename}: Shutterstock requires title <=2048 characters and 7–50 keywords")
        if not 1 <= len(m.categories) <= 2 or len(set(m.categories)) != len(m.categories) or any(c not in SHUTTERSTOCK_CATEGORIES for c in m.categories):
            raise ValueError(f"{m.filename}: select 1 or 2 marketplace categories")
        for value in (m.editorial, m.mature, m.illustration):
            flag(value)
    elif marketplace == "adobe":
        if len(m.filename) > 30 or len(m.caption) > 70 or len(m.keywords) > 50 or len(m.releases) > 30:
            raise ValueError(f"{m.filename}: Adobe CSV exceeds a verified field limit; see docs/platform-rules.md")
        if "," in m.caption:
            raise ValueError(f"{m.filename}: Adobe CSV titles must not contain commas")
        if m.category != "" and str(m.category) not in {str(n) for n in range(1, 22)}:
            raise ValueError("Adobe category must be blank or an ID from 1 to 21")
    else:
        flag(m.color)
    return m


def export_csv(records, marketplace: str) -> bytes:
    if marketplace not in SCHEMAS:
        raise ValueError(f"unknown marketplace: {marketplace}")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(SCHEMAS[marketplace])
    names = set()
    count = 0
    for record in records:
        m = validate(record, marketplace)
        if m.filename.casefold() in names:
            raise ValueError(f"duplicate filename: {m.filename}")
        names.add(m.filename.casefold())
        keywords = ", ".join(m.keywords)
        if marketplace == "shutterstock":
            row = [m.filename, m.caption, keywords, ",".join(m.categories), flag(m.illustration), flag(m.mature), flag(m.editorial)]
        elif marketplace == "adobe":
            row = [m.filename, m.caption, keywords, m.category, m.releases]
        else:
            row = [m.filename, m.caption, m.country, m.caption, keywords, m.color.lower()]
        # Reject formula-like cells rather than changing asset names or metadata.
        if any(str(cell).lstrip().startswith(("=", "+", "-", "@")) for cell in row):
            raise ValueError(f"{m.filename}: spreadsheet formula-like cell; revise metadata")
        writer.writerow(row)
        count += 1
    result = stream.getvalue().encode("utf-8")
    if marketplace == "adobe" and (count > 5000 or len(result) > 1_000_000):
        raise ValueError("Adobe CSV exceeds 5000 rows or 1 MB; split the batch")
    return result


def export_istock_zip(records) -> bytes:
    records = list(records)
    export_csv(records, "istock")  # validate duplicates across the whole batch
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for record in records:
            # Full basename avoids collisions between photo.jpg and photo.png.
            archive.writestr(record.filename + ".csv", export_csv([record], "istock"))
    return output.getvalue()


def main():
    import argparse
    import json
    from pathlib import Path
    import sys
    parser = argparse.ArgumentParser(description='Independent stock metadata CSV exporter')
    parser.add_argument('--input', required=True)
    parser.add_argument('--marketplace', required=True, choices=list(SCHEMAS))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    try:
        source = Path(args.input).resolve(strict=True)
        target = Path(args.output).absolute()
        if target.is_symlink() or target.exists() or target.suffix.lower() != '.csv':
            raise ValueError('output must be a new .csv path; overwriting is disabled')
        with source.open(encoding='utf-8-sig') as handle:
            rows = json.load(handle)
        if not isinstance(rows, list) or not rows:
            raise ValueError('input must be a nonempty JSON list of metadata objects')
        payload = export_csv([Metadata(**row) for row in rows], args.marketplace)
        with target.open('xb') as handle:
            handle.write(payload)
        print(f'Exported {len(rows)} records to {target}')
        return 0
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())