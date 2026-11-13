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
