## 19.0.0.0.4 (2026-10-02)

- **Fix (ANALYTICENFORCE-001): posting several invoices at once no longer
  fails.** With the validation enabled, posting two or more journal entries
  together (e.g. from the list view) raised *Expected singleton*, because the
  document type was read on the whole selection. Each vendor bill, refund or
  receipt is now validated separately; other document types in the same
  selection are posted without the check.

## 19.0.0.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
