# Stock Metadata Assistant v1.0.0-rc.1 — release evidence

Date: 2026-11-12 (America/Chicago). Scope: PR #1,
feat/agent-skill-modernization. Baseline reviewed: 8f2bec1f55e2ca090663bf154510fd014c8b601c.
The skill RC version is independent of the application's 1.5.0.dev0 version.

## Product-quality validation follow-up

The reproducible [benchmark framework](benchmark/README.md) now reserves **24
samples: 12 photographs and 12 illustrations**. No authorized manually labeled
dataset was supplied. Actual coverage is **0 labeled / 0 inferred / 0 assessed**;
all quality metrics are null, not invented zeros or benchmark successes. See the
[machine-readable report](benchmark/reports/not-tested.json) and matching
[Markdown report](benchmark/reports/not-tested.md). The prior three synthetic
smoke images remain separate historical execution evidence.

Added measurements cover supported/unsupported/uncertain caption claims, omitted
salient objects, human-rated keyword relevance, exact duplication, local per-site
structural compliance, timed review effort and edit operations. Humans must label
real images and assess raw outputs; these judgments are not inferred by unit tests.
Raw decoder captions and direct KeyBERT candidates/scores are stored separately
from corrected metadata, with source/dataset/review hash bindings and provenance.

The new export-reviewed route requires complete dataset assessment, named human
approval for the exact marketplace and metadata digest, all review checks resolved
and valid corrected CSV fields. It blocks the whole export on incomplete or invalid
records. Existing exporters remain backward-compatible **draft utilities**; CLI,
UI and skill now explicitly say that structural validity is not submission readiness.

Keyword candidate investigation is an evidence-bound experimental helper, not a
validated improvement or default change. It preserves provenance, requires human
review and never pads quotas. CLIP remains disabled, unvalidated and outside v1.0.

New [portal checklist/result template](portal-import-validation.md) and
[Agensi unpublished-draft checklist/result template](agensi-draft-validation.md)
mark authenticated/live actions **NOT TESTED**. They do not authorize uploads.

Local follow-up suite: **66 tests, 65 passed, 1 Windows symlink-permission skip**.
Benchmark unit fixtures validate arithmetic, coverage, immutable raw capture and
review gates; they are not real-world quality results. Latest commit CI evidence
is recorded in PR #1 after its jobs complete. Historical results below retain
their original scope. Updated ZIP/member hashes are in release-manifest.json.

**ACTION REQUIRED:** supply 20–30 authorized images with actual human labels
(planned balance 12+12), run cached inference, time real human review, adjudicate
uncertain claims and set product acceptance criteria before making quality claims.
Current templates/account imports, Agensi live validation and publication approval
remain external release gates. No stock content is submitted by these tools.

## Status matrix

| Status | Check | Evidence / boundary |
| --- | --- | --- |
| PASS | Full PR diff and all baseline tests reviewed | Core, CLI, three adapters, model wrapper, packaging, CI, dependency files, license, skill and documentation; findings below |
| PASS | Automated regression suite | 51 tests: 50 passed, 1 skipped on Windows Python 3.10.11; see validation.md |
| PASS | Real cached offline inference | BLIP and KeyBERT executed on 3 generated raster illustrations; raw outputs/timings/hashes in inference-results.json |
| FAIL | Unreviewed model output as submission-ready metadata | Flower drawing gained unsupported "flower shop" intent; abstract caption omitted rectangle; cup generated only 5 keywords (below Shutterstock's documented minimum) |
| PASS | Text-only/no-Python/no-vision/no-CLI trials | Actual constrained agent responses and rubric in agent-native-evaluation.md; not an Agensi live session |
| PASS | Independent script execution | Exact script bytes copied alone to a temporary directory, run with Python isolated mode; all three layouts and adversarial inputs tested |
| PASS | Package structure and local security checks | Five allowlisted UTF-8 text/code files, one SKILL.md, relative paths, under-20-KB script, fixed ZIP metadata, SHA-256 manifest; no bundled environments, weights, binaries or credentials |
| PASS | Frontmatter | Parsed with installed PyYAML safe_load; name, description, RC version, summary and tags present |
| PASS | Official schema documentation comparison | Current Adobe required/optional names and Shutterstock's explicit seven headers/order compared; see platform-rules.md |
| NOT TESTED | Downloaded current Adobe sample CSV bytes | Official link resolved, browser rejected text/csv; curl DNS failed. Do not claim byte-level template verification |
| NOT TESTED | Shutterstock sample CSV bytes | Current page enumerates schema but exposes no downloadable CSV sample in retrieved text |
| NOT TESTED | Adobe/Shutterstock authenticated import | No account import/upload performed; documentation matching cannot prove portal acceptance |
| NOT TESTED | iStock/ESP | Preserved legacy Creative Illustration layout only; no authenticated current template or vocabulary resolution |
| NOT TESTED | Live Agensi get_skill/execution/review | Packaging docs reviewed; no upload, scanner score, approval or live listing test |
| NOT TESTED | Photographic benchmark, GPU, fresh model downloads | Only cached CPU inference on synthetic illustrations; no photographic sample was available in scope |
| NOT TESTED | Comprehensive dependency vulnerability scan | pip check reports no broken requirements; that is dependency consistency, not a vulnerability assessment |
| ACTION REQUIRED | Release approval gates | Current-template comparison and portal tests; photographic smoke set; creator review of claims/licensing/price; explicit approval before merge or Agensi upload |

## Audit findings and fixes

1. Metadata dataclass annotations did not enforce runtime types. Nested category
   lists, null country and boolean category IDs could crash or serialize invalid
   cells. Add explicit checks and clear ValueErrors; cover isolated-script failures.
2. Adobe release values accepted arbitrary paths/non-JPEG filenames. Validate a
   basename and JPEG suffix when supplied. Exact portal match remains user review.
3. Portable basenames accepted reserved Windows device names and bidi controls.
   Reject these rather than changing source names. Extend formula-prefix rejection
   to a leading byte-order mark, keeping source names exact or rejecting export.
4. Streamlit state keyed only by filename could leak old metadata into a different
   upload with the same name. Bind state to SHA-256 upload contents, clear changed
   or removed metadata and reject case-colliding basenames before editing.
5. JSON duplicate keys silently overwrote data. Reject duplicate keys in both input
   routes; preserve explicit per-file recovery for the batch CLI.
6. Shipped script duplicated package logic without a generation check. Add a source
   generator and equality test; remove model/image/ZIP code from the standalone
   CSV script. Runtime remains entirely independent of package siblings.
7. ZIP timestamps depended on build time and lacked provenance. Fix timestamps and
   member permissions; add manifest hashes and repeat-build byte comparison.
8. Baseline schema tests mirrored production constants. Add literal header fixtures,
   actual demonstration-output comparisons, static no-network/no-shell checks and
   adversarial input cases. Restrict CI token to contents:read; upload review
   artifacts to GitHub Actions only. This does not upload anything to Agensi.
9. Skill guidance did not explicitly apply safety checks to manual CSV text. Add
   formula/path/duplicate checks and treat supplied descriptions as data. Verify
   behavior with a constrained text-only trial. Host agent adherence still varies.
10. Demo CSVs use csv.writer's CRLF endings. Preserve their bytes through Git
    attributes so Windows/Linux checkouts can verify actual exported samples
    without line-ending conversion changing the evidence.

All baseline test files were read in full. No unrelated user changes were present
at start. Root entry points and three exporters remain. Source image writes,
automatic EPS renaming, paid APIs and marketplace uploading are absent. Export
validation intentionally rejects unsafe/invalid cases rather than silently fixing
their filenames. The CLI assumes user-controlled directories; it is not a hardened
multi-user upload service and does not promise resistance to concurrent filesystem
replacement, unlimited hostile JSON or denial-of-service image inputs.

## Real inference versus mocks

Existing environment: Python 3.10.11, torch 2.6.0, transformers 4.52.4, KeyBERT
0.9.0, sentence-transformers 3.4.1, Pillow 11.3.0. No installation or cache edits
were required. HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE and telemetry opt-out variables
were set in the subprocess; backend used local_files_only=True. CPU inference
used existing model caches, not a credentialed or paid service.

BLIP revision 82a37760796d32b1411fe092ab5d4e227313294b was reported by the loaded
config; MiniLM cache snapshot was c9745ed1d9f207416be6d2e6f8de32d1f16199bf.
The cached BLIP snapshot includes pytorch_model.bin; no remote custom code was
enabled. This is execution evidence for existing trusted caches, not a claim
that arbitrary downloaded weights or every dependency is safe.

The final smoke run loaded models in 8.172 s and completed three images in
10.828 s total. Every source SHA-256 stayed unchanged. The smoke status PASS means
execution and immutability only. It does not score factual correctness, keyword
quality or platform eligibility. See raw captions and manual failure observations.
Ordinary unit/CI tests inject fake inference and do not load/download weights.

## Platform and licensing review

Current help-page sources and exact retrieval outcomes appear in platform-rules.md.
No claim covers a live authenticated service. Adobe special-character wording and
numeric category mapping still require portal/template review; no guessed ASCII
restriction or new unverified platform limit was introduced.

Project and bundled skill license notices match MIT copyright 2025 NYskytigers.
Only first-party source and stdlib exporter logic are bundled. The public model
cards list BLIP as BSD-3-Clause and MiniLM as Apache-2.0; no weights are distributed.
References: https://huggingface.co/Salesforce/blip-image-captioning-base and
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 . A future weight
redistribution requires reviewing exact model/dependency license texts, notices
and applicable platform terms separately. Do not market this MIT work as exclusive.

## Deliverables and reproduction

- docs/agensi-v1-listing.md: listing, compatibility, FAQ, limits, screenshot guidance,
  release notes, and publication boundaries.
- docs/demo/: input, proposed metadata, validation notes and actual CSV samples.
- docs/release-manifest.json: exact local RC package/member hashes and sizes.
- GitHub Actions: ZIP and manifest artifacts per OS/Python job; CI results belong
  to their commit SHA and are linked in PR #1 after the run finishes.

```sh
python tools/build_skill_script.py
python -m unittest discover -s tests -v
python -m compileall -q stock_metadata app.py models.py exporters.py tools
python tools/package_skill.py
# Separate real inference, only with installed dependencies and existing caches:
python tools/smoke_inference.py --output <new-report.json>
```

No new commit is called CI-verified until its remote jobs complete. No merge,
publication, Agensi upload, purchase, permissions grant or marketplace upload is
part of this release candidate preparation.
