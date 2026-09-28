# Changelog

## 19.0.1.0.2 (2026-09-28)

- Fix: the Hoot unit tests never ran. Hoot only executes modules whose name
  ends in `.test`, so `many2one_badge_field.test.esm.js` was loaded but
  silently skipped ("Passed 0 tests"). Renamed it to
  `many2one_badge_field.test.js`.
- Added `tests/test_js.py`, so the Hoot tests run with the Python test suite
  (and in CI).
- The edit mode test now checks removing the value, picking another partner
  from the autocomplete and saving; a new test checks that clicking the badge
  opens the color picker and writes the chosen color on the partner.
  The edit mode test is desktop only: on mobile the autocomplete opens a
  dialog instead of a dropdown.
