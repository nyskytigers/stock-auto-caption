# Full text-only demo

User: "Prepare Adobe metadata. I can't share images. mug.jpg shows a plain white
ceramic coffee mug on an oak table in natural window light. No logos, people or
release requirements. I want a CSV."

Agent: "I'll use your description; I haven't inspected the image. Based on the
2026-11-12 rule snapshot, this draft uses the Adobe CSV layout. Please confirm
your portal template if live rule lookup isn't available."

| Filename | Title | Ordered keywords | Category | Open checks |
| --- | --- | --- | --- | --- |
| mug.jpg | White ceramic coffee mug on an oak table | coffee mug, white, ceramic, oak table, natural light, window light, drinkware | 4 | Confirm visible details and category |

User confirms factual details and Drinks category. Agent prepares:

```json
[
  {
    "filename": "mug.jpg",
    "caption": "White ceramic coffee mug on an oak table",
    "keywords": ["coffee mug", "white", "ceramic", "oak table", "natural light", "window light", "drinkware"],
    "category": 4
  }
]
```

With no Python, deliver this CSV text for the user to save as UTF-8:

```csv
Filename,Title,Keywords,Category,Releases
mug.jpg,White ceramic coffee mug on an oak table,"coffee mug, white, ceramic, oak table, natural light, window light, drinkware",4,
```

With Python and file tools, save reviewed JSON to an explicit data path, copy the
bundled export script unchanged to a temporary script path, then execute:

```text
python <temporary-script.py> --input <reviewed.json> --marketplace adobe --output <new-mug.csv>
```

Delete the temporary script afterwards. Report the actual output path only after
successful execution. The script doesn't read or change mug.jpg, load a model,
or upload anything. Import into the portal and review before submission.

For the separate installed CLI, use keyed JSON instead:

```json
{
  "mug.jpg": {
    "caption": "White ceramic coffee mug on an oak table",
    "keywords": ["coffee mug", "white", "ceramic", "oak table", "natural light", "window light", "drinkware"],
    "category": 4
  }
}
```

```text
stock-metadata --input-dir <image-dir> --marketplace adobe --metadata-json <keyed.json> --output <outside-image-dir/new.csv>
```

If another filename lacks metadata, CLI writes valid rows, reports that filename
on stderr and exits 1. Correct the missing entry and rerun to a new output path.
If all entries fail or output exists, no new export is written and exit is 2.
