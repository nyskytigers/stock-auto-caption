# Product-quality benchmark protocol v1

Status: **NOT TESTED**. manifest.json reserves 24 slots, not 24 acquired/labeled
images. No third-party images were downloaded. The three earlier synthetic smoke
fixtures are not a photographic benchmark and are not counted in this dataset.

## Dataset and labels

Supply 12 owned/permitted photographs and 12 owned/permitted illustrations using
the 12 strata per kind in manifest.json. Keep difficult examples; freeze selection
before seeing model outputs. Each actual image needs exact basename, SHA-256,
documented rights basis/evidence, annotator/date and manually inspected labels.
A URL alone is not permission. Do not commit private images or releases.

List the 1–5 salient visible objects, visible attributes, relevant keyword concepts
and prohibited unsupported inferences. Add platform_fields.adobe/shutterstock
using Metadata keys (category/categories/flags/releases) for manually chosen fields.
Change status to labeled only after inspection. Labels are never fed to BLIP.
Freeze the manifest and preregister any acceptance targets before evaluating;
the framework does not invent quality thresholds or a product PASS score.

## Reproduce

```text
python -m stock_metadata.benchmark plan --output <new-plan-dir>
python -m stock_metadata.benchmark run --manifest <labeled.json> --images <owned-images> --output <new-run-dir>
python -m stock_metadata.benchmark report --manifest <same.json> --raw <run/raw.json> --review <human-review.json> --output <new-report-dir>
python -m stock_metadata.benchmark export-reviewed --manifest <same.json> --raw <run/raw.json> --review <human-review.json> --marketplace adobe --output <new-export-dir>
```

All 20–30 planned items must be labeled and rights-documented before CLI inference.
It uses separately installed cached offline models, never automatic downloads.
Use new output directories outside image directories. Each image is read only and
hash checked; symlinks/path traversal are rejected. Record environment/model-cache
versions, hardware and run IDs when comparing baseline/candidate runs.

raw.json preserves LocalBackend.generate_raw_caption decoded BLIP text before
normalization/refinement and direct KeyBERT candidates/scores before deduplication.
Injected test backends without that method use generate_caption, recorded in provenance.
This is not token-level tracing. Keep raw.json unchanged; edit its separate review
template. Digests bind the manifest, raw data and review; do not mix runs.

## Human annotation rubric

- caption_claims: enumerate every atomic assertion as text plus supported,
  unsupported or uncertain. Include count/color/action/location/commercial purpose.
  Unverified claims are uncertain, not correct. Confirm caption_exhaustive and
  objects_checked only after checking the entire caption and salient-object list.
- missing_objects: unique subset of canonical labels absent from the raw caption.
- keyword_judgments: relevant/irrelevant/uncertain for each raw occurrence in order.
  Judge useful evidence, not keyword quantity. Note semantic redundancy separately;
  exact-string duplicate counts do not detect wood versus wooden table.
- review_seconds: actual timed active review/edit duration, excluding breaks.
  edit_operations: count title replacements plus keyword additions/removals/reorders.
  Keep counting consistent and explain ambiguous judgments in notes. Never invent
  review time from text length. Record reviewer/date; adjudicate disagreement with
  another human before making quality claims.
- reviewed_metadata: separate corrected Metadata object. All facts/keywords/rights/
  editorial/releases/platform_fields checks must be explicitly true, with notes for
  not-applicable checks. unresolved must be empty; approved_marketplace must match
  the export. Set approved_metadata_sha256 = benchmark.digest(reviewed_metadata)
  only after approval. Editing metadata invalidates approval. This records a human
  attestation, not cryptographic proof that somebody reviewed an image.

## Measurements

| Metric | Denominator / meaning |
| --- | --- |
| Caption factual accuracy | Supported atomic claims / all judged claims |
| Hallucination | Unsupported claims / all judged claims |
| Uncertainty | Uncertain claims / all judged claims |
| Missing objects | Missing canonical salient objects / labels in assessed images |
| Keyword relevance | Relevant occurrences / all judged occurrences, including uncertain |
| Duplication | Case-insensitive exact duplicate occurrences / nonempty raw occurrences |
| Platform compliance | Pass fraction for local normalizing exporter validation, separately per site; not portal acceptance |
| Review effort | Mean measured seconds and edit operations; pending entries excluded |

JSON includes counts, per-item details, coverage by kind and provenance digests.
Markdown renders the same report. Empty denominators are null / NOT TESTED.
Partial coverage stays NOT TESTED. Inference errors remain FAIL records, not
zero-hallucination successes. ASSESSED means full coverage, not quality acceptance.
reports/not-tested.* contains no results. Unit fixtures are synthetic calculations,
not manually labeled benchmark evidence. Small samples do not establish reliability.

## Candidate investigation and review gate

KeyBERT cannot recover objects absent from a BLIP caption and can propose awkward
n-grams. Compare candidate strategies on the same frozen set using relevance,
object coverage and review effort, not keyword count. The experimental helper
stock_metadata.candidates.keyword_candidates merges model proposals with explicitly
human-confirmed visible terms, preserves provenance, deduplicates and marks every
term review_required. It does not pad quotas, expand categories or invent synonyms,
locations or visual facts. It is not a default behavior change or validated quality
improvement. Shortage of evidence means withhold submission, not manufacture terms.

CLIP stays outside v1.0, disabled and unvalidated. Any future ranking needs its own
independent comparison, model-license review and evidence.

Existing UI/CLI/standalone CSV tools remain backward-compatible draft utilities.
Structural validation is not human approval or submission readiness. The benchmark
export-reviewed command blocks the entire export for incomplete dataset coverage,
missing approval, unresolved checks, failed inference, changed approval digest or
invalid corrected fields. No command uploads or submits marketplace content.
