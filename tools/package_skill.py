"""Build an allowlisted text-only skill ZIP; no repository/environment sweep."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "stock-metadata-assistant"
FILES = ["SKILL.md", "LICENSE", "scripts/export_csv.py", "references/platform-rules.md", "references/demo.md"]


def main():
    target = ROOT / "dist" / "stock-metadata-assistant.zip"
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            source = SKILL / name
            if source.is_symlink():
                raise ValueError(f"symlink not allowed: {name}")
            text = source.read_text(encoding="utf-8")
            if name.endswith(".py") and len(text.encode("utf-8")) >= 20_000:
                raise ValueError("script exceeds review guideline")
            archive.writestr("stock-metadata-assistant/" + name, text.encode("utf-8"))
    print(target)


if __name__ == "__main__":
    main()
