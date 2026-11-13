# Adobe/Shutterstock import validation

Status: **NOT TESTED — authenticated access and explicit upload authorization required**.
This checklist does not authorize uploads or stock submission. Local schema checks
do not prove live portal acceptance. Repeat separately for each platform.

- [ ] Obtain explicit approval naming account, owned/permitted assets and CSV upload.
- [ ] Preserve originals; record rights evidence and source hashes.
- [ ] Download the current account template; record URL, time, exact headers and SHA-256.
- [ ] Compare encoding, categories, flags, limits and releases to current rules/template;
      resolve any conflict before import. platform-rules.md is only a dated starting point.
- [ ] Complete human factual/keyword/rights/release review and approval digest.
- [ ] Upload only authorized assets, then import only their matching CSV.
- [ ] Read back every image's exact filename/case/extension, title, keyword order/count,
      category, flags and exact release association. Record mismatches by row.
- [ ] Test permitted quoting and Unicode cases; do not upload dangerous formula cells.
- [ ] Save actual redacted messages/screenshots if authorized; do not invent success.
- [ ] Verify no stock content was submitted. Never press Submit in an import-only test.
- [ ] Record cleanup instructions; obtain approval before deleting account assets.

## Result template

```json
{
  "status": "NOT TESTED",
  "platform": "adobe_or_shutterstock",
  "tested_at": null,
  "tester": null,
  "authorization_reference": null,
  "account_label_redacted": null,
  "template_url": null,
  "template_sha256": null,
  "exact_headers": null,
  "commit": null,
  "csv_sha256": null,
  "source_manifest_sha256": null,
  "human_review_reference": null,
  "asset_upload_performed": false,
  "csv_import_performed": false,
  "rows_expected": null,
  "rows_matched": null,
  "field_checks": [],
  "portal_messages_verbatim_redacted": [],
  "evidence_paths": [],
  "stock_submission_performed": false,
  "cleanup_status": "NOT TESTED",
  "blockers": ["No authenticated account import or upload approval"]
}
```

PASS requires observed import and field readback for every expected row. Attempted
failure is FAIL; unavailable access is NOT TESTED. Record partial results honestly.
iStock/ESP remains legacy and unverified; this checklist does not establish support.
