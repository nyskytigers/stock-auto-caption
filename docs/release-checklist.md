# Release checklist

RC evidence lives in release-candidate.md. Checked local automation is not a
substitute for the unchecked live-service gates below. Skill version 1.0.0-rc.1
does not change the application's independent version number.

- [ ] Rebase/review against latest main; inspect the full diff and licenses.
- [ ] Run python -m unittest discover -s tests -v on Python 3.10–3.12, Windows/Linux.
- [ ] Install .[images] and .[ai,ui] in clean environments; run pip check.
- [ ] Run real BLIP/KeyBERT CPU smoke test with explicitly downloaded weights;
      repeat offline with cache, confirm no credentials and no source changes.
- [ ] Manually launch streamlit run app.py; edit all tabs, append batch fields,
      mix corrupt/valid images, verify previews, validation and three downloads.
- [ ] Compare marketplace CSV templates and rule pages; update dated references,
      constants and boundary tests together. Verify current ESP Creative Illustration
      template and controlled-vocabulary behavior in an authorized account.
- [ ] Try one real portal CSV per supported schema, without submitting content.
- [ ] Test skill with text-only agent, no Python/no vision; then run script copied
      unchanged to a temporary file from an unrelated directory.
- [ ] Build skill ZIP via python tools/package_skill.py; inspect allowlist and size.
- [ ] Confirm ZIP contains one skill, text only, MIT license, no weights, environments,
      images, caches, credentials or executable binaries.
- [ ] Review docs/validation.md actual results; distinguish mocks from real inference.
- [ ] Update version/changelog, regenerate dependency lock in validated ML environment.
- [ ] Review draft PR and CI, merge only after review; tag release deliberately.
- [ ] Obtain explicit approval before any Agensi publication; set listing price,
      support terms and capability claims only after testing in buyer workflow.
