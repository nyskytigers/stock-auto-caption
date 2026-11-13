# Actual validation evidence

## v1.0.0-rc.1 follow-up

2026-11-12, Windows Python 3.10.11: **51 tests, 50 passed, 1 skipped** (symlink
creation privilege). Full output was recorded during the RC run. Existing Pillow/Streamlit environment; pip check
reported no broken requirements. compileall and git diff --check passed.
Added isolated adversarial-input checks, literal headers and demo parity,
upload-cache invalidation, duplicate JSON rejection, generated-script parity,
reserved names, metadata types, deterministic ZIP and artifact manifest checks.

Real BLIP/KeyBERT offline inference now executed on three synthetic raster
illustrations: 3/3 completed, hashes unchanged. Actual captions include factual
errors. This is separate from fake-inference unit tests, not a photo benchmark.
See inference-results.json and release-candidate.md for exact scope and failures.
Final commit CI results are recorded in PR #1; the historical results below are
retained as earlier evidence rather than assertions about this RC commit.

---

Executed 2026-11-12 on Windows, Python 3.10.11.

## Automated results

- Bare system Python: initial suite 34 tests, 31 passed, 3 skipped in 0.968 s.
  Pillow was absent and Windows symlink creation lacked privilege.
- Existing local application environment (Pillow 11.3.0, Streamlit 1.50.0):
  Final run: 39 tests, 38 passed, 1 skipped (Windows symlink privilege) in 1.528 s.
- Real Pillow decoding: generated RGBA image becomes full-resolution RGB;
  source SHA-256 stays unchanged. A corrupt image does not prevent the next
  valid image from processing. Inference uses an injected fake, not real BLIP.
- CLI subprocess: metadata-only export, exact original basename, source hash
  unchanged, whitespace paths. Unit/integration checks cover partial failures,
  missing metadata, malformed JSON, output protection and backend failure.
- CSV checks: three schemas, quoting, exact filenames, ordered keyword cleanup,
  proper-name preservation, boundary limits, duplicates, formula-like fields,
  error placeholders and iStock same-stem ZIP collisions.
- UI: actual Streamlit AppTest empty page renders without model loading;
  adapter tests exercise all three downloads with edited session state, batch
  append, blocked invalid metadata and mixed corrupt/valid image editors.
- Agensi script: copied unchanged into an isolated temporary directory, all
  three schemas match the package byte-for-byte; invalid paths and overwrite
  attempts fail. Package allowlist, UTF-8, script size and frontmatter checked.
- compileall and git diff --check passed after whitespace cleanup.

## Not executed / release gates

No real BLIP/KeyBERT inference or CLIP model evaluation. No authenticated
marketplace import, current ESP template retrieval or live Agensi execution.
No manual browser interaction with uploaded images. CI matrix is committed;
its remote result must be checked on the draft PR. No claim of cross-platform
execution here beyond this Windows Python 3.10 run.

Pip and Git network attempts failed on this host (DNS/transport). The existing
application environment supplied image/UI dependencies without modifying it.
GitHub's connector supplies the feature-branch commit using the true upstream
parent, avoiding the local reconstructed snapshot history.

## Reproduce

```sh
python -m pip install -e ".[images,ui]"
python -m unittest discover -s tests -v
python -m compileall -q stock_metadata app.py models.py exporters.py
python tools/package_skill.py
git diff --check
```

See release-checklist.md for remaining manual, model and portal checks.
