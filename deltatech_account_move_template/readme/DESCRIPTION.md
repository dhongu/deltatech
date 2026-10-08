This module lets the accountant define journal entry templates once and
generate the entries from a wizard by entering only the base amounts and the
date. Odoo itself only lets you duplicate an existing entry and edit every line.

**Key features:**

- A template has a journal, a default reference, instructions for the user and
  lines with account, label, optional partner, analytic distribution, taxes or
  tax grids, and a direction (debit or credit).
- Each line has a code (e.g. `GROSS`, filled in as `L1`, `L2`... when left
  empty) and an amount type:
  - **Entered**: typed in when the entry is generated. The suggested value is
    a fixed amount or a formula (e.g. `GROSS * 0.25`) that the user can
    override.
  - **Fixed**: always the same amount.
  - **Percentage**: a percentage of another line.
  - **Formula**: a Python expression on the codes of the other lines, with
    `round`, `abs`, `min` and `max`.
  - **Balance**: the amount that balances the entry, taxes included.
- Lines without an account are parameters of the computation (an amount
  including VAT, a rate): they are entered or computed, but not recorded.
- The computation order follows the formulas, not the line order; unknown
  codes, loops and invalid formulas are refused when the template is saved.
- Taxes on a line work as on a manual journal entry: Odoo adds the tax lines
  with their tax grids, so the entry is included in the VAT return, and the
  balance line takes the tax into account.
- A negative amount goes on the other side of its account; lines with a zero
  amount are skipped.
- The generated entry keeps a link to its template: a **From Template** filter
  on the journal entries and an **Entries** button on the template.
- For companies with Romania as fiscal country, **Load Romanian Templates**
  creates ready-made templates: monthly rent as tenant and as lessor, manual
  depreciation of tangible and intangible assets, assets received for use
  (loan for use or rent, off-balance), payroll from an external payslip, meal
  vouchers and the cash basis VAT adjustments.
