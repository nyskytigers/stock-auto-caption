"""Generate the shipped single-file exporter; runtime never reads siblings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAIL = '''
def main():
    import argparse
    import json
    from pathlib import Path
    import sys
    parser = argparse.ArgumentParser(description="Independent stock metadata CSV exporter")
    parser.add_argument("--input", required=True)
    parser.add_argument("--marketplace", required=True, choices=list(SCHEMAS))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        source = Path(args.input).resolve(strict=True)
        target = Path(args.output).absolute()
        if target.is_symlink() or target.exists() or target.suffix.lower() != ".csv":
            raise ValueError("output must be a new .csv path; overwriting is disabled")
        with source.open(encoding="utf-8-sig") as handle:
            rows = json.load(handle, object_pairs_hook=unique_json_object)
        if not isinstance(rows, list) or not rows:
            raise ValueError("input must be a nonempty JSON list of metadata objects")
        if any(not isinstance(row, dict) for row in rows):
            raise ValueError("each metadata row must be an object")
        payload = export_csv([Metadata(**row) for row in rows], args.marketplace)
        with target.open("xb") as handle:
            handle.write(payload)
        print(f"Exported {len(rows)} records to {target}")
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
'''


def contents():
    core = (ROOT / "stock_metadata/core.py").read_text(encoding="utf-8")
    core = core.split("\ndef refine_caption(")[0]  # no model/image code in skill
    export = (ROOT / "stock_metadata/csv_export.py").read_text(encoding="utf-8")
    export = export.replace("from .core import Metadata\n", "")
    export = export.replace("import zipfile\n", "")
    export = export.replace("            from .core import safe_filename\n", "")
    export = export.split("\ndef export_istock_zip(")[0]
    return "# MIT License; Copyright (c) 2025 NYskytigers. See bundled LICENSE.\n" + core + "\n" + export + "\n" + TAIL


if __name__ == "__main__":
    target = ROOT / "skills/stock-metadata-assistant/scripts/export_csv.py"
    target.write_text(contents(), encoding="utf-8", newline="\n")
