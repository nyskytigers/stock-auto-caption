# Agensi listing draft — v1.0.0-rc.1

Status: unpublished release candidate. Skill version is separate from the existing
application's 1.x version. Do not tag, merge, upload or publish from this document.

## Name and short description

**Stock Metadata Assistant**

Turn factual image descriptions into reviewable stock titles, ordered keywords
and CSV metadata while keeping original filenames intact.

## Listing description

Prepare stock metadata with your AI agent, even when it cannot view your images.
Provide exact filenames and factual descriptions; the assistant drafts concise
titles, removes duplicate keywords, flags missing facts and prepares CSV text for
Adobe Stock or Shutterstock using dated platform references.

You keep control of the final metadata. The assistant won't invent an unknown
image's contents or fill a keyword quota with guesses. A small optional Python
exporter validates fields and creates UTF-8 CSV files without sending data to an
external API. It runs independently from a temporary file and needs no installed
application, model weights or paid credentials.

For users who separately install Stock-Auto-Caption, an optional local BLIP and
KeyBERT backend can propose captions and keywords from raster images. That backend
is **not included in this skill ZIP**, is not required for drafting and can make
factual mistakes. Every record still needs your review.

Includes one agent skill, a self-contained exporter, platform-rule references,
a complete worked example and the MIT license. Legacy iStock Creative Illustration
export remains available experimentally; current ESP compatibility is unverified.

## Compatibility statement

| Capability | Requirements | Scope / actual evidence |
| --- | --- | --- |
| Agent-native drafting | Agent can read text instructions and user descriptions | Actual constrained text-only trials; no Python/vision/CLI required |
| CSV text delivery | Agent can output text | Save manually as UTF-8 if no file tool exists |
| Standalone CSV script | Python 3.10+ and temporary-script execution | Stdlib only; tested in isolation; no package siblings |
| Optional local image inference | Separately installed app AI extra, model caches, suitable RAM | Real offline CPU run on synthetic illustrations; no photographic benchmark |
| Streamlit UI | Separately installed app AI/UI extras | Local automated UI tests; not bundled in skill |
| Agensi delivery | Compatible agent and Agensi account workflow | Documentation reviewed; no live Agensi-hosted test or approval |
| iStock | Current ESP account template / vocabulary resolution | Legacy Creative Illustration only; unverified live import |

No blanket claim covers every agent product. An agent's own execution permissions,
context limits and file access determine which optional features it can use.

## FAQ

**Do I need Python or a GPU?** No for metadata drafting and CSV text. Python is
optional for file export. Local BLIP inference is a separate installation; the
smoke test used CPU, not GPU.

**Can it see my images?** Only if your agent has visual access. Otherwise it asks
for descriptions and states that it has not inspected the image.

**Does the ZIP contain BLIP?** No. It contains text and a small export script.
No models, virtual environments, binaries or credentials are bundled.

**Will my files change?** The exporter does not open or write images. It preserves
basenames and extensions, rejects unsafe names and refuses to overwrite outputs.
The installed CLI also keeps generated output outside the input directory.

**Is it private/offline?** The standalone exporter has no network code. Your host
agent's privacy terms apply to descriptions/attachments. Local inference uses the
host machine and may download model files initially; a hosted Streamlit app
receives uploads on its server. Don't call every workflow fully offline.

**Does it guarantee acceptance or sales?** No. Rights, releases, facts, technical
quality, controlled vocabulary and current portal requirements need review.
No auto-submission is included.

**Why doesn't it always generate 50 keywords?** Fewer relevant terms are better
than invented ones. A platform minimum can require more user-supplied evidence;
the assistant reports that rather than padding the list.

**Is iStock supported?** Only a preserved legacy Creative Illustration layout.
Do not advertise current ESP, photo, video or editorial compatibility without a
template and live account test.

**What am I licensing?** The code and skill are MIT licensed, including permission
to use, modify and redistribute with the required notice. Do not claim exclusive
or proprietary rights. Any Agensi purchase/delivery terms and pricing require
creator review; no price is chosen here. Model weights have separate licenses.

## Limitations to display before purchase

- Metadata is a review draft, not verified image truth or legal clearance.
- Adobe's linked sample CSV was not retrievable in this environment; comparison
  with the actual current downloaded template remains open.
- Live Adobe/Shutterstock/ESP imports and Agensi loading have not been tested.
- Cached offline BLIP ran on three synthetic illustrations, with factual errors;
  photographic subject coverage and fresh-install/download behavior remain untested.
- CLIP relevance is a future design, not a feature in v1.0.
- Browser/file/Python capability varies by host agent.

## Screenshot and demo guidance

Prepare actual screenshots only after running the corresponding workflow. Show:

1. A text-only user description alongside the title/keyword review table. Label
   "No visual inspection — based on user-provided facts."
2. The CSV text with exact original filenames and a withheld unknown-image row.
3. A terminal run of the independent script copied to a temporary directory,
   showing the exit status and resulting header; hide personal local paths.
4. The validation error for an invalid filename or formula-like field.

Use docs/demo/walkthrough.md as the script. If demonstrating optional BLIP, label
the separate installation, show the raw output and the human correction side by
side. Do not show marketplace acceptance badges, Agensi approval or invented UI
screenshots. Screenshot capture and a recorded walkthrough remain to be produced;
no simulated image is evidence of a successful service test.

## Release notes draft

v1.0.0-rc.1 of the skill introduces text-first metadata drafting, current linked
rule references, exact source basenames, an independent stdlib exporter, explicit
validation failures and a full demonstration. The application modernization keeps
three UI exporters and adds a reusable Python package and CLI.

RC hardening adds metadata type validation, safe release filenames, reserved-name
and formula checks, upload-content cache invalidation, duplicate JSON-key rejection,
deterministic ZIPs with SHA-256 manifests and additional regression tests.
No merge, publication, pricing, service purchase or permissions change is included.
