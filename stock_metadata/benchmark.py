"""Opt-in, local benchmark tooling. No images or quality scores are fabricated."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import importlib.metadata
import json
import math
import re
from pathlib import Path
import sys

from .core import Metadata, safe_filename, unique_json_object
from .csv_export import export_csv

VERSION = 1
CHECKS = ("facts", "keywords", "rights", "editorial", "releases", "platform_fields")


def read_json(path):
    with Path(path).open(encoding="utf-8-sig") as source:
        return json.load(source, object_pairs_hook=unique_json_object)


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as target:
        json.dump(value, target, indent=2, ensure_ascii=True, allow_nan=False)
        target.write("\n")


def validate_manifest(manifest):
    if manifest.get("schema_version") != VERSION or not isinstance(manifest.get("items"), list):
        raise ValueError("expected schema_version 1 and items list")
    if not 20 <= len(manifest["items"]) <= 30:
        raise ValueError("product benchmark must reserve 20–30 items")
    seed = manifest.get("seed", 0)
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError("seed must be an integer in the unsigned 32-bit range")
    ids, filenames = set(), set()
    for item in manifest["items"]:
        identifier = safe_filename(item["id"])
        if identifier in ids or item.get("kind") not in {"photograph", "illustration"}:
            raise ValueError("duplicate ID or invalid image kind")
        ids.add(identifier)
        if item.get("status") == "labeled":
            filename = safe_filename(item["filename"])
            if filename.casefold() in filenames:
                raise ValueError("duplicate source basename")
            filenames.add(filename.casefold())
            rights = item.get("rights", {})
            if rights.get("basis") not in {"user_owned", "explicit_permission", "public_domain_verified"} or not rights.get("evidence"):
                raise ValueError("labeled image needs an explicit rights basis and evidence")
            labels = item.get("labels", {})
            if not labels.get("annotator") or not labels.get("labeled_at") or not labels.get("objects"):
                raise ValueError("manual labels need annotator, date and visible objects")
            if not all(isinstance(o, str) and o.strip() for o in labels["objects"]):
                raise ValueError("objects must be nonempty text labels")
            if len({o.casefold() for o in labels["objects"]}) != len(labels["objects"]):
                raise ValueError("canonical object labels must be unique")
            if not isinstance(item.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
                raise ValueError("labeled image needs its source SHA-256")
        elif item.get("status") != "pending":
            raise ValueError("status must be pending or labeled")
    return manifest


def plan():
    strata = ["single object", "multiple objects", "indoor scene", "outdoor scene",
              "low light", "busy background", "small object", "text or logo",
              "unusual viewpoint", "negative space", "fine detail", "ambiguous subject"]
    return {"schema_version": VERSION, "dataset_id": "stock-metadata-quality-v1",
            "status": "NOT TESTED", "seed": 0,
            "selection_policy": "12 photographs + 12 illustrations; no internet image acquisition; manual labels before model output",
            "items": [{"id": f"{kind[:5]}-{i+1:02d}", "kind": kind, "stratum": stratum,
                       "status": "pending", "filename": None, "sha256": None,
                       "rights": {"basis": None, "evidence": None},
                       "labels": {"annotator": None, "labeled_at": None, "objects": [],
                                  "visible_attributes": [], "forbidden_inferences": [], "relevant_keyword_concepts": []}}
                      for kind in ("photograph", "illustration") for i, stratum in enumerate(strata)]}


def run(manifest, image_dir, backend):
    validate_manifest(manifest)
    root = Path(image_dir).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("images must be a directory")
    records = []
    from PIL import Image, ImageOps
    for item in manifest["items"]:
        if item["status"] != "labeled":
            continue
        path = root / item["filename"]
        result = {"id": item["id"], "filename": item["filename"], "source_sha256": item["sha256"]}
        try:
            if path.is_symlink() or not path.is_file() or path.resolve().parent != root:
                raise ValueError("source must be a direct regular child; symlinks are rejected")
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            if before != item["sha256"]:
                raise ValueError("source hash differs from manual-label manifest")
            with Image.open(path) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
            try:
                generate = getattr(backend, "generate_raw_caption", backend.generate_caption)
                caption = generate(image)
                result["caption"] = caption  # retain BLIP output even if keyword extraction fails
                candidates = backend.kw_model.extract_keywords(caption, keyphrase_ngram_range=(1, 2), stop_words="english", top_n=25)
            finally:
                image.close()
            result.update(caption=caption, keywords=[term for term, _ in candidates],
                          keyword_scores=[float(score) for _, score in candidates])
            if hashlib.sha256(path.read_bytes()).hexdigest() != before:
                raise ValueError("source hash changed during inference")
            result["source_unchanged"] = True
        except Exception as error:
            result["error"] = str(error)
        records.append(result)
    versions = {}
    for dependency in ("torch", "transformers", "keybert", "sentence-transformers", "Pillow"):
        try:
            versions[dependency] = importlib.metadata.version(dependency)
        except importlib.metadata.PackageNotFoundError:
            versions[dependency] = None
    keyword_embedding = getattr(getattr(backend, "kw_model", None), "model", None)
    keyword_revision = None
    try:
        keyword_revision = keyword_embedding.embedding_model._first_module().auto_model.config._commit_hash
    except AttributeError:
        pass
    return {"schema_version": VERSION, "dataset_sha256": digest(manifest), "records": records,
            "provenance": {"backend": type(backend).__name__, "python": sys.version.split()[0],
                           "seed": manifest.get("seed", 0),
                           "keyword_parameters": {"ngram_range": [1, 2], "stop_words": "english", "top_n": 25},
                           "dependencies": versions, "keyword_revision": keyword_revision,
                           "device": str(getattr(getattr(backend, "model", None), "device", "not reported")),
                           "blip_revision": getattr(getattr(getattr(backend, "model", None), "config", None), "_commit_hash", None),
                           "caption_stage": "raw decoder output for LocalBackend; generate_caption fallback for injected backends; before refinement",
                           "keyword_stage": "direct KeyBERT candidates and scores before deduplication; no padding"}}


def assessment_template(raw):
    return {"schema_version": VERSION, "raw_sha256": digest(raw), "assessments": [
        {"id": row["id"], "status": "pending", "reviewer": None, "reviewed_at": None,
         "caption_claims": [], "missing_objects": None, "keyword_judgments": None,
         "caption_exhaustive": False, "objects_checked": False,
         "review_seconds": None, "edit_operations": None, "unresolved": ["Human review required"],
         "checks": {key: False for key in CHECKS}, "reviewed_metadata": None}
        for row in raw["records"]]}


def assess_row(item, row, assessment):
    if assessment.get("status") != "complete":
        raise ValueError("assessment is pending")
    if not assessment.get("reviewer") or not assessment.get("reviewed_at"):
        raise ValueError("reviewer identity and date required")
    if assessment.get("caption_exhaustive") is not True or assessment.get("objects_checked") is not True:
        raise ValueError("human must confirm exhaustive caption/object assessment")
    claims = assessment.get("caption_claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("human must enumerate caption claims")
    for claim in claims:
        if not isinstance(claim, dict) or not claim.get("text") or claim.get("verdict") not in {"supported", "unsupported", "uncertain"}:
            raise ValueError("each claim needs text and supported/unsupported/uncertain verdict")
    missing = assessment.get("missing_objects")
    if not isinstance(missing, list) or len(set(missing)) != len(missing) or any(obj not in item["labels"]["objects"] for obj in missing):
        raise ValueError("missing objects must be a unique subset of manual labels")
    judgments = assessment.get("keyword_judgments")
    if not isinstance(judgments, list) or len(judgments) != len(row.get("keywords", [])):
        raise ValueError("judge each raw keyword occurrence in order")
    if any(j not in {"relevant", "irrelevant", "uncertain"} for j in judgments):
        raise ValueError("invalid keyword judgment")
    for name in ("review_seconds", "edit_operations"):
        value = assessment.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be an actual nonnegative measurement")
        if name == "edit_operations" and not isinstance(value, int):
            raise ValueError("edit_operations must be an integer count")
    return claims, missing, judgments


def report(manifest, raw, review):
    validate_manifest(manifest)
    if raw.get("schema_version") != VERSION or review.get("schema_version") != VERSION:
        raise ValueError("unsupported raw/review schema version")
    if raw.get("dataset_sha256") != digest(manifest) or review.get("raw_sha256") != digest(raw):
        raise ValueError("dataset/raw/review hash binding failed")
    labels = {i["id"]: i for i in manifest["items"]}
    rows = raw.get("records", [])
    if len({r["id"] for r in rows}) != len(rows) or any(r["id"] not in labels or labels[r["id"]]["status"] != "labeled" for r in rows):
        raise ValueError("raw IDs must uniquely match labeled items")
    assessments = review.get("assessments", [])
    if len({a["id"] for a in assessments}) != len(assessments) or any(a["id"] not in {r["id"] for r in rows} for a in assessments):
        raise ValueError("duplicate or unknown assessment ID")
    by_id = {a["id"]: a for a in assessments}
    totals = Counter()
    details = []
    seconds, edits = [], []
    for row in rows:
        item = labels[row["id"]]
        detail = {"id": row["id"], "kind": item["kind"], "status": "NOT TESTED", "raw_platform_checks": {}}
        if row.get("source_sha256") != item["sha256"] or row.get("filename") != item["filename"]:
            raise ValueError("raw source identity does not match labeled item")
        if "error" in row:
            detail.update(status="FAIL", error=row["error"])
            details.append(detail)
            continue
        if not isinstance(row.get("caption"), str) or not isinstance(row.get("keywords"), list) or any(not isinstance(k, str) for k in row["keywords"]):
            raise ValueError("raw caption must be text and raw keywords a text list")
        for site in ("adobe", "shutterstock"):
            try:
                # Category choices belong to manual labels, never model inference.
                options = item.get("platform_fields", {}).get(site, {})
                export_csv([Metadata(row["filename"], row["caption"], row["keywords"], **options)], site)
                detail["raw_platform_checks"][site] = {"status": "PASS", "scope": "local structural validation only"}
            except (ValueError, TypeError) as error:
                detail["raw_platform_checks"][site] = {"status": "FAIL", "error": str(error)}
            totals[site + "_checked"] += 1
            totals[site + "_passed"] += detail["raw_platform_checks"][site]["status"] == "PASS"
        keys = [k.strip().casefold() for k in row["keywords"] if k.strip()]
        detail["raw_duplicate_occurrences"] = len(keys) - len(set(keys))
        totals["duplicate_occurrences"] += detail["raw_duplicate_occurrences"]
        totals["raw_keywords"] += len(keys)
        assessment = by_id.get(row["id"], {})
        if assessment.get("status") == "complete":
            claims, missing, judgments = assess_row(item, row, assessment)
            totals.update(c["verdict"] for c in claims)
            totals["claims"] += len(claims)
            totals["objects"] += len(item["labels"]["objects"])
            totals["missing_objects"] += len(missing)
            totals.update("keyword_" + j for j in judgments)
            totals["judged_keywords"] += len(judgments)
            seconds.append(assessment["review_seconds"])
            edits.append(assessment["edit_operations"])
            detail["status"] = "ASSESSED"
            detail["human_metrics"] = {"claims": dict(Counter(c["verdict"] for c in claims)), "missing_objects": missing,
                                      "keyword_judgments": dict(Counter(judgments)), "review_seconds": seconds[-1], "edit_operations": edits[-1]}
        details.append(detail)
    ratio = lambda n, d: n / d if d else None
    assessed = sum(d["status"] == "ASSESSED" for d in details)
    complete = assessed == len(manifest["items"])
    return {"schema_version": VERSION, "status": "ASSESSED" if complete else "NOT TESTED",
            "scope": "human judgments plus local validator snapshot, not live portal acceptance",
            "dataset_sha256": digest(manifest), "raw_sha256": digest(raw), "review_sha256": digest(review),
            "coverage": {"planned": len(manifest["items"]), "labeled": sum(i["status"] == "labeled" for i in manifest["items"]),
                         "inferred": len(rows), "human_assessed": assessed,
                         "by_kind": {kind: {"planned": sum(i["kind"] == kind for i in manifest["items"]),
                                             "assessed": sum(d["kind"] == kind and d["status"] == "ASSESSED" for d in details)} for kind in ("photograph", "illustration")}},
            "counts": dict(totals),
            "metrics": {"caption_supported_claim_rate": ratio(totals["supported"], totals["claims"]),
                        "hallucinated_claim_rate": ratio(totals["unsupported"], totals["claims"]),
                        "uncertain_claim_rate": ratio(totals["uncertain"], totals["claims"]),
                        "missing_object_rate": ratio(totals["missing_objects"], totals["objects"]),
                        "keyword_relevance_rate": ratio(totals["keyword_relevant"], totals["judged_keywords"]),
                        "keyword_uncertain_rate": ratio(totals["keyword_uncertain"], totals["judged_keywords"]),
                        "raw_adobe_structural_pass_rate": ratio(sum(d["raw_platform_checks"].get("adobe", {}).get("status") == "PASS" for d in details), sum("adobe" in d["raw_platform_checks"] for d in details)),
                        "raw_shutterstock_structural_pass_rate": ratio(sum(d["raw_platform_checks"].get("shutterstock", {}).get("status") == "PASS" for d in details), sum("shutterstock" in d["raw_platform_checks"] for d in details)),
                        "raw_duplicate_rate": ratio(totals["duplicate_occurrences"], totals["raw_keywords"]),
                        "mean_review_seconds": ratio(sum(seconds), len(seconds)),
                        "mean_edit_operations": ratio(sum(edits), len(edits))}, "items": details}


def markdown(result):
    lines = ["# Product-quality benchmark", "", f"Status: **{result['status']}**", "", result["scope"], "",
             "## Coverage", "", "```json", json.dumps(result["coverage"], indent=2), "```", "",
             "## Metrics", "", "Rates use assessed denominators; null means NOT TESTED, never zero quality.", "",
             "| Metric | Value |", "| --- | --- |"]
    lines += [f"| {key} | {'NOT TESTED' if value is None else round(value, 4)} |" for key, value in result["metrics"].items()]
    lines += ["", "## Items", "", "| ID | Kind | Assessment | Adobe local check | Shutterstock local check |", "| --- | --- | --- | --- | --- |"]
    for row in result["items"]:
        checks = row["raw_platform_checks"]
        lines.append(f"| {row['id']} | {row['kind']} | {row['status']} | {checks.get('adobe', {}).get('status', 'NOT TESTED')} | {checks.get('shutterstock', {}).get('status', 'NOT TESTED')} |")
    return "\n".join(lines) + "\n"


def export_reviewed(manifest, raw, review, site):
    result = report(manifest, raw, review)  # verify provenance and completed metric entries
    if result["coverage"]["human_assessed"] != len(manifest["items"]):
        raise ValueError("benchmark dataset incomplete; reviewed export blocked")
    items = {i["id"]: i for i in manifest["items"]}
    assessments = {a["id"]: a for a in review["assessments"]}
    records = []
    for row in raw["records"]:
        a = assessments.get(row["id"], {})
        if "error" in row or row.get("source_unchanged") is not True or a.get("status") != "complete":
            raise ValueError(f"{row['id']}: inference/review incomplete; export blocked")
        if a.get("unresolved") != [] or any(a.get("checks", {}).get(k) is not True for k in CHECKS):
            raise ValueError(f"{row['id']}: human checks unresolved; export blocked")
        if a.get("approved_marketplace") != site:
            raise ValueError("human approval must name the exact marketplace")
        values = a.get("reviewed_metadata")
        if not isinstance(values, dict) or values.get("filename") != items[row["id"]]["filename"]:
            raise ValueError("reviewed metadata must preserve the exact source filename")
        if a.get("approved_metadata_sha256") != digest(values):
            raise ValueError("approval digest must match reviewed metadata; re-review after editing")
        records.append(Metadata(**values))
    if not records:
        raise ValueError("no reviewed records to export")
    return export_csv(records, site)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "run", "report", "export-reviewed"])
    parser.add_argument("--manifest")
    parser.add_argument("--raw")
    parser.add_argument("--review")
    parser.add_argument("--images")
    parser.add_argument("--output", required=True, help="new output directory; existing directories are never overwritten")
    parser.add_argument("--marketplace", choices=["adobe", "shutterstock"])
    args = parser.parse_args(argv)
    try:
        output = Path(args.output)
        if output.exists() or output.is_symlink():
            raise ValueError("output must be a new directory")
        if args.command == "plan":
            output.mkdir()
            write_new(output / "manifest.json", plan())
        else:
            if not args.manifest:
                raise ValueError("--manifest is required")
            manifest = validate_manifest(read_json(args.manifest))
            if args.command == "run":
                if not args.images:
                    raise ValueError("--images is required")
                if any(i["status"] != "labeled" for i in manifest["items"]):
                    raise ValueError("label and authorize all planned items before the product run")
                if Path(args.images).resolve() in output.resolve().parents:
                    raise ValueError("benchmark outputs must be outside image directory")
                from .backends import LocalBackend
                import random
                import torch
                random.seed(manifest.get("seed", 0))
                torch.manual_seed(manifest.get("seed", 0))
                raw = run(manifest, args.images, LocalBackend(local_files_only=True))
                output.mkdir()
                write_new(output / "raw.json", raw)
                write_new(output / "review.json", assessment_template(raw))
            else:
                if not args.raw or not args.review:
                    raise ValueError("--raw and --review are required")
                raw, review = read_json(args.raw), read_json(args.review)
                if args.command == "report":
                    result = report(manifest, raw, review)
                    output.mkdir()
                    write_new(output / "report.json", result)
                    (output / "report.md").write_text(markdown(result), encoding="utf-8")
                else:
                    if not args.marketplace:
                        raise ValueError("--marketplace is required")
                    payload = export_reviewed(manifest, raw, review, args.marketplace)
                    output.mkdir()
                    (output / "reviewed.csv").write_bytes(payload)
        return 0
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
