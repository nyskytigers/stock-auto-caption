# Stock-Auto-Caption

Local BLIP captions, KeyBERT keywords and reviewable stock metadata exports.
Existing Streamlit application and Shutterstock, Adobe Stock and legacy iStock
Creative Illustration exports remain available. No paid API or credentials needed.

## Install and run

Python 3.10+:

```sh
git clone https://github.com/nyskytigers/stock-auto-caption.git
cd stock-auto-caption
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[ai,ui]"
streamlit run app.py
```

The existing `pip install -r requirements.txt` route still works. The checked-in
requirements-lock.txt describes an older environment; regenerate it only after a
clean model smoke test. This change keeps existing model version constraints,
rather than combining architecture changes with an untested ML upgrade.

For metadata-only CLI/package usage, `pip install -e .` installs no runtime
dependencies. Add `.[images]` for decoding images, or `.[ai]` for local inference.
First model initialization may download BLIP and MiniLM weights. Subsequent
offline use requires their complete caches; no offline guarantee on a fresh install.

## Architecture and compatibility

- `stock_metadata/core.py`: caption/keyword normalization, metadata records and
  read-only full-resolution RGB/EXIF-aware image processing.
- `stock_metadata/csv_export.py`: shared field validation, UTF-8 CSV and iStock ZIP.
- `stock_metadata/backends.py`: opt-in BLIP/KeyBERT, no Streamlit dependency.
- `stock_metadata/cli.py`: deterministic, nonrecursive batch workflow.
- Root `app.py`, `models.ModelLoader` and three exporter classes retain their
  entry points. UI edits and batch append controls remain available.

Original filenames and extensions now remain exact. EPS rewriting was a bug:
this software never converted rasters into vectors. Invalid fields block export
instead of truncating or padding metadata. Proper-name capitalization is retained;
category names no longer become speculative keywords. iStock ZIP entries now use
the complete basename, such as `photo.jpg.csv`, avoiding same-stem collisions.

## CLI demo

Create `reviewed.json` using exact filenames that exist directly in your image
directory:

```json
{
  "mug.jpg": {
    "caption": "White ceramic coffee mug on an oak table",
    "keywords": ["coffee mug", "white", "ceramic", "oak table", "natural light", "window light", "drinkware"],
    "category": 4,
    "categories": ["Objects"]
  }
}
```

```sh
stock-metadata --input-dir ./photos --marketplace adobe --metadata-json ./reviewed.json --output ./adobe.csv
stock-metadata --input-dir ./photos --marketplace shutterstock --metadata-json ./reviewed.json --output ./shutterstock.csv
stock-metadata --input-dir ./photos --marketplace istock --metadata-json ./reviewed.json --istock-zip --output ./istock.zip
# Explicit opt-in: local model inference, potentially downloads weights
stock-metadata --input-dir ./photos --marketplace adobe --local-ai --output ./generated.csv
# Equivalent without installing the console entry point:
python -m stock_metadata --help
```

Quote paths containing spaces. `--categories "Objects,Nature"` overrides
Shutterstock categories; `--category 4` overrides the Adobe category. The iStock
CLI defaults to one CSV; `--istock-zip` matches the legacy per-image ZIP workflow.

Only direct JPG/JPEG/PNG children are considered. Supplied-metadata mode checks
file presence and paths but deliberately does not decode images or infer their
contents. Local-AI mode decodes before inference. Unsupported extensions are
ignored. No image is written, renamed or embedded with metadata. Symlink sources
are rejected; output must be new, have the right extension and sit outside the
input directory. Output parents must already exist. Exclusive creation prevents
overwrites; this is designed for user-controlled directories, not adversarial
concurrent filesystem mutation.

Per-file failures appear as JSON objects on stderr. Valid rows still export:
exit 0 = all processed successfully, 1 = partial batch, 2 = fatal/no valid rows.
A final JSON summary reports exported and failed counts. No retry loop or uploads.
Fix errors and rerun to a new output path.

## Marketplace scope

| Export | Layout | Remaining review |
| --- | --- | --- |
| Shutterstock | Filename, Description, Keywords, Categories, Illustration, Mature Content, Editorial | Relevance, category choices, editorial facts and rights |
| Adobe | Filename, Title, Keywords, Category, Releases | Plain-text title, uploaded release files, current template |
| iStock | file name, description, country, title, keywords, color | Legacy Creative Illustration only; verify current ESP template and controlled vocabulary |

See [dated rule sources and validation boundaries](docs/platform-rules.md).
No unverified iStock numeric limits are enforced. The existing schema is documented
by DeepMeta 3, which is unsupported; current ESP acceptance needs account testing.
Do not advertise universal iStock photo/video compatibility.

## Agensi skill

[skills/stock-metadata-assistant/SKILL.md](skills/stock-metadata-assistant/SKILL.md)
provides a text-first agent workflow, a full demo and an independent stdlib export
script. It works from user descriptions without Python, BLIP or visual access.
Its optional installed CLI is a separate capability.

```sh
python tools/package_skill.py
```

Creates `dist/stock-metadata-assistant.zip` from an explicit text-only allowlist.
No environments, model weights, executables, images or credentials are packaged.
Scripts run independently when copied unchanged to temporary files, per Agensi's
rules. The standalone script takes a JSON list, unlike the CLI's keyed object.
See [full demo](skills/stock-metadata-assistant/references/demo.md).
Nothing publishes to Agensi automatically.

The current skill is **v1.0.0-rc.1**, separate from the application's version.
See [release evidence](docs/release-candidate.md), [listing/FAQ draft](docs/agensi-v1-listing.md)
and [complete demonstration](docs/demo/walkthrough.md). Builds now include a SHA-256
manifest alongside the ZIP; fixed timestamps make repeated builds reproducible in
the same Python/zlib environment. CI uploads the ZIP and manifest as workflow
artifacts for review, never to Agensi.

## Privacy and limitations

Local inference runs on the machine hosting Python. First use downloads models
from their hosts. The core CSV tools and standalone script make no network calls.
The UI loads a Google Font; browsers may contact Google. A hosted Streamlit app
receives images on its host, so it is not equivalent to running on your computer.
Agent-native prompts and attachments follow the agent provider's privacy policy.
No telemetry or marketplace uploader is added.

AI can hallucinate and KeyBERT cannot recover visual details absent from the
caption. Review every record. Validators cannot establish rights, releases,
editorial accuracy, platform acceptance or keyword relevance. BLIP inference can
be slow on CPU. [Optional CLIP relevance enhancement](docs/clip-design.md) is a
design only, with no mandatory dependencies or bundled weights.

## Tests and release

```sh
python -m pip install -e ".[images]"
python -m unittest discover -s tests -v
python -m compileall -q stock_metadata app.py models.py exporters.py
python tools/package_skill.py
```

Tests use fake inference backends, generated tiny images and temporary directories;
they do not download models or contact marketplaces. Image tests skip if Pillow
is absent; UI adapter tests skip if Streamlit/Pillow is absent. CI installs those
dependencies in separate jobs. See [actual validation results](docs/validation.md),
[audit and plan](docs/audit-and-plan.md) and [release checklist](docs/release-checklist.md).

The separately invoked `tools/smoke_inference.py --output <new-report.json>` runs
real cached BLIP/KeyBERT offline. It is excluded from unit tests and ordinary CI.
Actual outputs and fixture scope live in docs/inference-results.json; a successful
smoke run does not establish factual accuracy or marketplace acceptance.

## License

[MIT](LICENSE), including the skill and exporter script. BLIP, MiniLM, model weights
and third-party dependencies have their own licenses; review their model cards
and terms before redistributing them. Users retain responsibility for their
images, permissions and releases.

