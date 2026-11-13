"""Pure metadata normalization and optional read-only image processing."""
from dataclasses import dataclass, field
import re
import unicodedata
from pathlib import Path


def unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def clean_caption(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("caption must be text")
    if any(unicodedata.category(c) == "Cc" and not c.isspace() for c in value):
        raise ValueError("metadata text contains a control character")
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
    stem = value.split(".", 1)[0].upper()
    if stem in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError("filename uses a reserved Windows device name")
    if any(unicodedata.bidirectional(c) in {"RLO", "LRO", "RLE", "LRE", "PDF", "RLI", "LRI", "FSI", "PDI"} for c in value):
        raise ValueError("filename contains a bidirectional control character")
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
        if not isinstance(self.categories, (list, tuple)) or any(not isinstance(c, str) for c in self.categories):
            raise ValueError("categories must be a list of category names")
        if isinstance(self.category, bool) or not isinstance(self.category, (str, int)):
            raise ValueError("category must be a text or integer category ID")
        for name in ("releases", "country", "editorial", "mature", "illustration", "color"):
            if not isinstance(getattr(self, name), str):
                raise ValueError(f"{name} must be text")
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
    name = safe_filename(filename or (Path(source).name if isinstance(source, (str, Path)) else source.name))
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
        image.load()
    try:
        caption = backend.generate_caption(image)
        caption, keywords = backend.refine_caption_and_keywords(caption, [])
        return Metadata(name, caption, keywords).normalized()
    finally:
        image.close()
