# Changelog

## 19.0.1.0.6 (2026-09-25)

- Fix: the category sequence could propose an internal reference that was
  already used. Its counter does not know about codes created outside the
  sequence (catalog imports, supplier invoice imports, mass renumbering,
  manually typed codes), so "New internal code" and automatic coding on
  product creation failed with "Internal Reference already exists". When the
  proposed code is taken (including by archived products or other companies),
  the sequence is now moved past the highest number already used with its
  prefix/suffix and the next number is taken. Sequences with date ranges are
  not synchronised. Ported from the Agroamat project.
