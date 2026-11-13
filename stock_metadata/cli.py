"""Read-only batch CLI. Exit 0 success, 1 partial batch, 2 fatal error."""
import argparse
import json
from pathlib import Path
import sys
from .core import Metadata, process_image
from .csv_export import export_csv, export_istock_zip, validate


def run_batch(input_dir, marketplace, backend=None, metadata=None, categories=(), category=""):
    root = Path(input_dir).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("input must be a directory")
    records, errors = [], []
    paths = sorted(root.iterdir(), key=lambda p: p.name.casefold())
    for path in paths:
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        try:
            if path.is_symlink() or not path.is_file() or path.resolve().parent != root:
                raise ValueError("symlink or non-regular source is not allowed")
            if metadata is not None:
                if path.name not in metadata:
                    raise ValueError("no supplied metadata for this filename")
                values = dict(metadata[path.name])
                if "filename" in values:
                    raise ValueError("metadata must not override filename")
                record = Metadata(filename=path.name, **values)
            else:
                record = process_image(path, backend, filename=path.name)
            if categories:
                record.categories = list(categories)
            if category != "":
                record.category = category
            record = validate(record, marketplace)
            # Catch cell validation before adding the row to a partial batch.
            export_csv([record], marketplace)
            if any(r.filename.casefold() == record.filename.casefold() for r in records):
                raise ValueError("duplicate filename under case-insensitive matching")
            records.append(record)
        except Exception as error:
            errors.append({"filename": path.name, "error": str(error)})
    return records, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--marketplace", required=True, choices=["shutterstock", "adobe", "istock"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--metadata-json", help="UTF-8 object keyed by exact filename; avoids model loading")
    parser.add_argument("--local-ai", action="store_true", help="explicitly load local models (may download weights)")
    parser.add_argument("--categories", default="", help="comma-separated Shutterstock category names")
    parser.add_argument("--category", default="", help="Adobe category ID")
    parser.add_argument("--istock-zip", action="store_true", help="legacy per-image Creative Illustration CSV ZIP")
    args = parser.parse_args(argv)
    try:
        if bool(args.metadata_json) == args.local_ai:
            raise ValueError("choose exactly one of --metadata-json or --local-ai")
        if args.istock_zip and args.marketplace != "istock":
            raise ValueError("--istock-zip requires --marketplace istock")
        root = Path(args.input_dir).resolve(strict=True)
        output = Path(args.output).absolute()
        if output.is_symlink() or output.exists():
            raise ValueError("output exists; choose a new path (overwriting is disabled)")
        if output.suffix.lower() != (".zip" if args.istock_zip else ".csv"):
            raise ValueError("output extension must match CSV or requested ZIP")
        # Keep generated artifacts out of source directories, including junctions.
        resolved = output.resolve()
        if resolved == root or root in resolved.parents:
            raise ValueError("output must be outside the input directory")
        metadata = None
        backend = None
        if args.metadata_json:
            with open(args.metadata_json, encoding="utf-8-sig") as source:
                metadata = json.load(source)
            if not isinstance(metadata, dict):
                raise ValueError("metadata JSON must be an object keyed by filename")
        else:
            from .backends import get_local_backend
            backend = get_local_backend()
        records, errors = run_batch(root, args.marketplace, backend, metadata,
                                    [c.strip() for c in args.categories.split(",") if c.strip()], args.category)
        for error in errors:
            print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        if not records:
            raise ValueError("no valid images/metadata; no output written")
        payload = export_istock_zip(records) if args.istock_zip else export_csv(records, args.marketplace)
        with output.open("xb") as target:
            target.write(payload)
        print(json.dumps({"exported": len(records), "failed": len(errors), "output": str(output)}))
        return 1 if errors else 0
    except (OSError, ValueError, TypeError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
