"""Bind UI metadata to upload contents, not just a reusable filename."""
import hashlib
from .core import safe_filename


def sync_uploads(files, state):
    current = {}
    names = set()
    for file in files:
        name = safe_filename(file.name)
        if name.casefold() in names:
            raise ValueError(f"Duplicate upload basename: {name}. Select distinct files before editing.")
        names.add(name.casefold())
        current[name] = hashlib.sha256(file.getvalue()).hexdigest()
    previous = state.get("stock_upload_hashes", {})
    for name in set(previous) | set(current):
        if previous.get(name) != current.get(name):
            for prefix in ("sh_", "ad_", "is_"):
                for field in ("caption_", "keywords_", "filename_"):
                    state.pop(prefix + field + name, None)
    state["stock_upload_hashes"] = current
