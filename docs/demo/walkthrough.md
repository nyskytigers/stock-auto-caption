# v1.0 release candidate demonstration

This is an agent-native **text description** demonstration. No images are supplied,
no vision is claimed, and the proposed metadata is not BLIP output.

## Inputs

User: "Prepare Adobe and Shutterstock metadata for these files. mug.JPG is a photo
of a plain white ceramic coffee mug on an oak table in natural window light, no
logos or people. abstract.png is my raster illustration of a red circle overlapping
a blue rectangle on a white background. mystery.png is an image I cannot describe.
I confirm Objects/Drinks for the cup and Abstract/Graphic Resources for the shapes."

The agent states that it relies on the user's description. It asks for missing
content facts for mystery.png and excludes it from final export until resolved.
The user reviews the proposed titles/keywords in reviewed.json. The agent does
not infer capture date, location, ownership or legal release eligibility.

| File | Proposed title | Validation notes |
| --- | --- | --- |
| mug.JPG | White ceramic coffee mug on an oak table | Exact uppercase extension; 7 supplied-fact keywords; Adobe category 4; Shutterstock Objects; photo flag No |
| abstract.png | Red circle overlapping a blue rectangle on white | Original extension; 7 relevant keywords; Adobe category 8; Shutterstock Abstract; illustration Yes |
| mystery.png | Withheld | No content evidence; do not invent a title or pad keywords |

Both accepted titles fit the dedicated Adobe CSV guidance's 70-character cap and
contain no commas. Numeric limits remain a dated policy snapshot. Category IDs
retain the app's mapping and need comparison with the portal's current template.
No release filename is supplied; blank does not prove a release is unnecessary.
Neither image's technical eligibility or legal rights has been inspected.

## No Python, no vision, no CLI

The agent can present the metadata table and the exact CSV text from adobe.csv or
shutterstock.csv. It says "Save this as UTF-8" instead of claiming it created a
file. It cites the dated rule snapshot when live browsing is unavailable. This is
an instructional walkthrough, complemented by actual text-only agent trial records
in ../agent-native-evaluation.md. No Agensi-hosted session is implied.

## Independent script execution

Fetch scripts/export_csv.py from the skill; copy its full bytes unchanged to a
temporary script, without sibling files. Run from an unrelated directory:

```text
python <temporary.py> --input <absolute-reviewed.json> --marketplace adobe --output <new-adobe.csv>
python <temporary.py> --input <absolute-reviewed.json> --marketplace shutterstock --output <new-shutterstock.csv>
```

Remove the temporary script after execution. The committed sample CSVs are actual
outputs of that shipped script. Integration tests compare them byte-for-byte to
the reusable package and verify security rejection paths. No asset upload occurs.

## Optional installed local inference

This is a separate capability. Install the application's AI extra first and
explicitly choose --local-ai. Cached offline inference of three generated fixtures
is recorded in ../inference-results.json; those captions are not substituted for
the human-reviewed samples here. Known real-model errors include a fabricated
flower-shop purpose and an omitted rectangle. Review before export.

## Portal follow-up (not performed)

Download the current account template, compare exact headers, upload matching
assets, import the CSV and inspect each applied field without pressing Submit.
That requires an authorized account and separate permission to upload. This
demonstration does not establish live portal acceptance.
