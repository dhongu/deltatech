## 19.0.0.0.6 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.0.5 (2026-10-03)

- **Fix (ANALYTICENFORCE-002): the validation follows the company of the
  bill.** The *Enable Analytic Distribution Validation* switch was read from
  the current company of the user, so a bill of a company with the validation
  enabled could be posted without analytic distribution while another company
  was selected, and the reverse. Each vendor bill, refund or receipt is now
  checked against the switch of its own company, also in a mixed-company
  batch. Users working in several companies may now be blocked on bills that
  were accepted before (or the other way round), according to each company's
  setting.

## 19.0.0.0.4 (2026-10-02)

- **Fix (ANALYTICENFORCE-001): posting several invoices at once no longer
  fails.** With the validation enabled, posting two or more journal entries
  together (e.g. from the list view) raised *Expected singleton*, because the
  document type was read on the whole selection. Each vendor bill, refund or
  receipt is now validated separately; other document types in the same
  selection are posted without the check.

## 19.0.0.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
