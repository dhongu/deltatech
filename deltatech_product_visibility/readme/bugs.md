# Bug review — Product Website Visibility Score

Review date: 2026-10-02. Target version: Odoo 19.

## VISIBILITY-001 — P2: Negative criterion weights break the advertised zero-to-one-hundred score

- **Status:** Open.
- **Location:** models/visibility_criterion.py, weight; models/product_template.py, _compute_website_visibility().
- **Trigger:** A system administrator enters a negative weight on an active criterion through the editable criterion list or ORM.
- **Actual behavior:** The integer field has no nonnegative constraint. The compute adds signed weights to the denominator and earned score without validating/clamping the resulting value. Product score can exceed 100 or become negative, while classification still marks scores above 90 as optimal.
- **Evidence:** Complete module models/views/ACL/data read. Executed the actual AST-extracted score and level methods with active weights SEO=100 and main_image=-90, only SEO satisfied: website_visibility_score=1000 and level=optimal. No database criterion mutation executed.
- **Impact:** The progress bar/badge and attention filters can report impossible scores and incorrect levels. The advertised normalized 0–100 interpretation no longer holds for configuration values the model permits.
- **Suggested fix:** Enforce nonnegative weights server-side, define the zero-total policy, and handle existing invalid weights before recomputing stored scores.
- **Validation needed:** Negative weight create/write rejected, zero weights/all-zero configuration, valid totals other than 100, and migration/recompute of previously invalid criteria.

## Review limitations

All eligible Python/XML source was read. Score computation was executed only with mock records. The module intentionally provides a manual recompute action after criterion changes, so the lack of automatic criterion-weight recomputation was not reported as an unconditional defect. No Odoo integration/access/database tests executed.
