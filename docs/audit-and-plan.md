# Audit and implementation plan

Baseline: upstream main c95cb2c95601aedecad90b3ad938dafe8710658e.
The local working copy was reconstructed through GitHub's connector because Git
transport failed. Its initial local commit is a snapshot, not upstream history;
the remote modernization commit must use the real upstream commit as parent.

## Findings

- Three UI exporters in exporters.py; every export changed extensions to EPS.
- UI, PIL, pandas and model loading were coupled; no reusable package or CLI.
- Shutterstock's Mature content header used incorrect case; flag ordering differed
  from the current documented template.
- iStock uses Creative Illustration fields, not a universal photo schema. ZIP
  member names based only on stems collide for image.jpg and image.png.
- Caption capitalization destroys proper names; arbitrary 150-character truncation
  loses information; category names polluted keywords.
- UI thumbnails were passed to inference; corrupt image decoding happened outside
  per-file error handling; Error placeholders could become exported metadata.
- CHANGELOG.md contains unresolved conflict markers. No tests or CI.
- requirements.txt and historical requirements-lock.txt include old model/UI stacks;
  fast BLIP preprocessing may require missing torchvision. Lock omits torchvision.
- Page configuration occurred after model construction; stylesheet used cwd.

## Phases

1. Extract pure normalization, validation, CSV, read-only image processing and lazy
   optional model backend. Keep root app.py, models.py and exporter classes.
2. Add CLI with explicit backend selection, exact basenames, exclusive output
   creation outside input, structured per-file errors and deterministic ordering.
3. Add Agensi text-first workflow and independent stdlib CSV script; document
   sources, constraints, privacy, licensing, demo and optional CLIP design.
4. Test pure core, CLI subprocesses, UI adapters and images with fake models;
   package only allowed skill files; add cross-platform CI and release checklist.

## Compatibility decisions

Keep all three tabs, editing/batch controls, local BLIP/KeyBERT and iStock ZIP.
Intentionally fix EPS rewriting rather than preserve incorrect asset references.
Validation now blocks invalid exports; no silent truncation, keyword padding or
filename changes. iStock ZIP member names include the complete source basename.
No marketplace upload or Agensi publication occurs automatically.

Do not upgrade all ML packages during this structural change: retain constraints,
use the slow BLIP processor and validate newer stacks in a separate model smoke
test before altering compatibility. requirements-lock.txt remains historical;
it is not advertised as a new reproducible environment.
