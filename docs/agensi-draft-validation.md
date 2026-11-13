# Agensi unpublished-draft validation

Status: **NOT TESTED for Agensi-hosted operations**. This checklist does not authorize
draft creation, uploads, purchases, permissions grants, submission or publication.

## Local checks

- [ ] Match version, listing claims, license notices and reviewed commit.
- [ ] Record ZIP/member SHA-256, sizes and allowlisted paths.
- [ ] Verify frontmatter, one skill, text references and absence of weights, binaries,
      environments, credentials, private images and benchmark data from the ZIP.
- [ ] Run exact standalone script alone from a temporary directory.
- [ ] Test text-only drafting, unknown images, keyword shortage, formula/path rejection
      and explicit review language without Python/vision/CLI.
- [ ] Report benchmark coverage honestly; do not equate synthetic tests with photo accuracy.
- [ ] Recheck official packaging/review documentation before any approved account action.

Local evidence is in release-candidate.md. These reusable unchecked boxes are not
new test results or a claim of scanner approval.

## Account actions — only with explicit approval

- [ ] Confirm that an unpublished-draft workflow exists before uploading. If an action
      would publish or submit for review automatically, stop and request a decision.
- [ ] Obtain approval naming exact ZIP digest and listing text.
- [ ] Create/upload only the explicitly authorized unpublished draft.
- [ ] Record actual file-tree/frontmatter interpretation and scanner warnings verbatim.
- [ ] Verify draft visibility and absence of publication/review submission.
- [ ] Execute only an available, authorized draft-preview path. No preview means
      NOT TESTED; do not claim get_skill or live execution from local tests.
- [ ] Save actual redacted evidence. Publication requires separate approval.
      Do not purchase a listing to manufacture execution evidence.

## Result template

```json
{
  "status": "NOT TESTED",
  "tested_at": null,
  "tester": null,
  "commit": null,
  "zip_sha256": null,
  "authorization_reference": null,
  "documentation_checked_at": null,
  "draft_created": false,
  "upload_performed": false,
  "visibility_observed": null,
  "scanner_result": null,
  "draft_preview_available": null,
  "actual_execution_trace": null,
  "published": false,
  "purchase_performed": false,
  "evidence_paths": [],
  "blockers": ["No authorized Agensi unpublished-draft test performed"]
}
```
