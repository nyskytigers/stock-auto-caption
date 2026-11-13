"""Build an allowlisted text-only skill ZIP; no repository/environment sweep."""
from pathlib import Path
import zipfile
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "stock-metadata-assistant"
FILES = ["SKILL.md", "LICENSE", "scripts/export_csv.py", "references/platform-rules.md", "references/demo.md"]


def main():
    target = ROOT / "dist" / "stock-metadata-assistant.zip"
    target.parent.mkdir(exist_ok=True)
    if target.is_symlink() or target.parent.is_symlink():
        raise ValueError("ZIP destination cannot be a symlink")
    payloads = {}
    for name in FILES:
        source = SKILL / name
        if not source.resolve().is_relative_to(SKILL.resolve()) or any(p.is_symlink() for p in [source, *source.parents] if p != ROOT.parent):
            raise ValueError(f"symlink or escaped source not allowed: {name}")
        text = source.read_text(encoding="utf-8")
        if name.endswith(".py") and len(text.encode("utf-8")) >= 20_000:
            raise ValueError("script exceeds review guideline")
        payloads[name] = text.encode("utf-8")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            entry = zipfile.ZipInfo("stock-metadata-assistant/" + name, date_time=(2020, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, payload)
    manifest = {"artifact": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "size_bytes": target.stat().st_size, "files": {name: {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for name, data in payloads.items()}}
    target.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
