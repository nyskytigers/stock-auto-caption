"""Verified CSV layouts; no pandas or Streamlit dependency.

Rule provenance and verification date: docs/platform-rules.md.
Validation rejects invalid data instead of changing filenames or truncating fields.
"""
import csv
import io
import zipfile
from .core import Metadata

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
