# Marketplace rule provenance

Verified 2026-11-12. Recheck before release; validators are a dated snapshot,
not a promise that a portal will accept content. Required fields, filenames and
CSV quoting are machine checked; relevance, rights, English grammar, editorial
date/location, technical image eligibility and release validity need human review.

## Shutterstock

- [Official CSV layout](https://submit.shutterstock.com/help/en/articles/10617486-how-do-i-include-existing-metadata-with-my-content-submission):
  Filename, Description, Keywords, Categories; optional Illustration, Mature Content,
  Editorial, with Yes/No values. Assets must already exist in the current submission.
- [Official metadata standards](https://submit.shutterstock.com/help/en/articles/10617427-content-publishing-standards-contextual-metadata):
  description at most 2048 characters; 7–50 relevant keywords; 1–2 categories
  from the listed names. Do not pad sparse metadata to reach the minimum.
  Documentary editorial captions require actual capture date and location.

## Adobe Stock

- [Official CSV requirements](https://helpx.adobe.com/stock/contributor/manage-your-portfolio/csv-requirements-content.html):
  exact filename including extension; title and keywords required; optional category
  and releases. UTF-8 CSV, at most 5000 data rows and 1 MB. This implementation
  conservatively treats MB as 1,000,000 encoded bytes.
- Current page lists filename 30 characters, title 70 characters, 50 keywords,
  release filename 30 characters. Title must use plain text without commas or
  special characters. We check commas/length and formula risks; ambiguous
  "special characters" needs portal review, not a guessed ASCII-only restriction.
- [Official create-CSV instructions and template](https://helpx.adobe.com/stock/contributor/manage-your-portfolio/create-csv-file.html):
  use Filename,Title,Keywords,Category,Releases, unchanged.
- [Category list](https://helpx.adobe.com/stock/contributor/content-policies-guidelines/metadata/choose-right-category-content.html):
  existing ordered 21-category mapping retained. Confirm IDs in the portal/template.
  Blank category is allowed in the CSV. Releases are exact uploaded JPEG release
  filenames, not arbitrary release titles.
- Other Adobe guidance/model templates may disagree on keyword/title limits. This
  implementation uses the current dedicated CSV page above. Stop and compare the
  actual portal template if it differs; do not silently overwrite policy constants.

## iStock / Getty

- [DeepMeta publisher's import guide](https://www.deepmeta.com/3/userguide/import-files)
  documents the preserved fields file name,description,country,title,keywords,color
  for **Creative Illustration**. Creative Image and Editorial Image use different
  columns. DeepMeta 3 is now unsupported; this is historical format evidence,
  not verification of every current ESP or DeepMeta 4 batch.
- No authenticated current ESP template was available during this audit. The legacy
  exporter remains available and is labeled accordingly. Obtain a current template
  from your own batch before uploading. No unverified numeric iStock limits are coded.
- Keywords require Getty controlled-vocabulary resolution. Country remains blank
  unless supplied; complete required portal fields. Color defaults to yes for
  backwards compatibility; set no for monochrome work. No automatic submission.

## Agensi

- [Packaging](https://www.agensi.io/docs/packaging) and
  [loading/execution](https://www.agensi.io/docs/how-agents-load-skills):
  ZIP containing SKILL.md with name and description; text/code resources only are
  needed here. Every script must run unchanged alone from a temporary file without
  importing or reading bundled siblings. No bundled dependencies, model weights,
  environments, binaries or credentials. Script logic should stay under 20 KB.
  Check current upload limits on that page before submitting.
