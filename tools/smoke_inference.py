"""Explicit offline real-model smoke test; not part of ordinary unit tests.

Generates three synthetic raster fixtures, not a photographic benchmark.
Uses existing caches only and records actual model outputs, hashes and failures.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "DO_NOT_TRACK"):
        os.environ[name] = "1"
    from PIL import Image, ImageDraw
    import importlib.metadata
    import tempfile
    report = {"kind": "real offline inference", "python": platform.python_version(),
              "fixture_scope": "synthetic raster illustrations only; no photo quality claim",
              "versions": {n: importlib.metadata.version(n) for n in ("torch", "transformers", "keybert", "sentence-transformers", "Pillow")},
              "results": []}
    start = time.monotonic()
    try:
        from stock_metadata.backends import LocalBackend
        from stock_metadata import process_image
        backend = LocalBackend(local_files_only=True)
        report["model_revision"] = getattr(backend.model.config, "_commit_hash", None)
        report["device"] = str(next(backend.model.parameters()).device)
        report["load_seconds"] = round(time.monotonic() - start, 3)
        with tempfile.TemporaryDirectory() as temp:
            for name in ("cup.png", "flower.png", "abstract.png"):
                image = Image.new("RGB", (480, 360), "white")
                draw = ImageDraw.Draw(image)
                if name == "cup.png":
                    draw.rectangle((0, 240, 480, 360), fill=(152, 111, 75))
                    draw.ellipse((270, 120, 345, 225), outline="black", width=12)
                    draw.rounded_rectangle((140, 110, 290, 260), radius=20, fill="white", outline="black", width=4)
                    draw.ellipse((140, 95, 290, 135), fill=(70, 40, 20), outline="black", width=4)
                elif name == "flower.png":
                    draw.line((240, 180, 240, 330), fill="black", width=5)
                    for x, y in ((190, 120), (250, 120), (160, 175), (280, 175), (190, 225), (250, 225)):
                        draw.ellipse((x-25, y-25, x+25, y+25), outline="black", width=4)
                    draw.ellipse((215, 150, 265, 200), fill="black")
                else:
                    draw.rectangle((30, 40, 220, 260), fill="blue")
                    draw.ellipse((180, 90, 420, 330), fill="red")
                path = Path(temp) / name
                image.save(path)
                image.close()
                before = hashlib.sha256(path.read_bytes()).hexdigest()
                tick = time.monotonic()
                try:
                    result = process_image(path, backend, name)
                    report["results"].append({"filename": name, "caption": result.caption,
                        "keywords": result.keywords, "seconds": round(time.monotonic()-tick, 3),
                        "source_sha256": before, "unchanged": before == hashlib.sha256(path.read_bytes()).hexdigest()})
                except Exception as error:
                    report["results"].append({"filename": name, "error": str(error)})
        report["status"] = "PASS" if all("error" not in r and r["unchanged"] for r in report["results"]) else "FAIL"
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = f"{type(error).__name__}: {error}"
    report["total_seconds"] = round(time.monotonic() - start, 3)
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True), flush=True)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
