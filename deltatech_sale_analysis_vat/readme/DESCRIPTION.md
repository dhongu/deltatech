Adds a VAT dimension to the standard sales analysis reports, so the turnover of a
period can be broken down by VAT rate without leaving the pivot views.

**Invoice Analysis** (`account.invoice.report`) gains:

- **VAT Rate** (tax group) and **VAT** (tax) as filter and group by;
- **Invoice for Fiscal Receipt** — flags invoices issued for an existing Point of Sale
  order, with filters to show or hide them. This is what keeps the turnover from being
  counted twice when the invoice analysis is read next to the Point of Sale analysis:
  the value of such an invoice is already part of the fiscal receipt.

**Point of Sale Analysis** (`report.pos.order`) gains:

- **VAT Rate** and **VAT** as filter and group by;
- **Receipts without Invoice** / **Receipts with Invoice** filters.

Only percentage taxes are treated as VAT. Fixed taxes (green tax, deposit return
scheme) are ignored, so every line keeps exactly one VAT rate and no line is
duplicated in the reports.

Turnover of a period, without duplication, is the Point of Sale Analysis filtered on
"Receipts without Invoice" plus the whole Invoice Analysis for customer invoices.
