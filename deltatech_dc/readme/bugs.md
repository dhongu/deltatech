# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## DC-001 — P2: Printing lot/invoice declarations fails without a production date

- **Status:** Open.
- **Location:** report/report_dc.py, ReportDCLotPrint and ReportDCInvoicePrint declaration creation.
- **Trigger:** Print a declaration for a lot with no production_date and no existing declaration, directly or from an invoiced lot.
- **Actual behavior:** Both report paths explicitly pass date=lot.production_date into create. production_date is optional, so False overrides the date field's context_today default even though declaration date is required. Creation fails instead of printing. The picking report already uses production_date or fields.Date.today().
- **Evidence:** All report paths and field declarations inspected; explicit false date bypasses the required field default. No report render/database create executed.
- **Impact:** Normal lots without the custom optional production date cannot obtain declarations through these report actions.
- **Suggested fix:** Define a consistent fallback declaration date and avoid passing false into a required field; align lot/invoice/picking paths.
- **Validation needed:** Lot with/without production date and existing declaration, invoice containing such lots, and picking fallback; all supported print paths must produce a valid declaration.

## DC-002 — P2: Generated declarations use current company instead of source company

- **Status:** Open.
- **Location:** report/report_dc.py, lot/invoice/picking search/create paths; views/report_dc.xml.
- **Trigger:** A user has companies A and B allowed, current company A, and prints a company-B invoice, picking or lot declaration.
- **Actual behavior:** Declaration creation omits company_id and does not switch company context, so the required company defaults to env.company A. Searches also omit company scope. The main report prints issuer fields through res_company rather than each declaration's company_id.
- **Evidence:** Full create/search dictionaries and QWeb issuer expressions inspected. Source document company is available but never used for these declarations. Company rule allows all currently allowed companies and therefore does not enforce matching source/declaration company. No multi-company database print executed.
- **Impact:** A document for company B may create/reuse a company-A declaration and print the wrong issuer, making the generated conformity document inconsistent with the source transaction.
- **Suggested fix:** Pass/scope source company on declaration search/create and render each declaration's company as issuer; handle mixed-company batches per document.
- **Validation needed:** Current company different from document company, same product/date in two companies, lot declarations and mixed-company print batches; verify declaration ownership and printed issuer.

## Review limitations

All eligible Python/XML source manually reviewed: declaration numbering, product standards, production/expiry dates, lot/invoice/picking report providers, report layouts, warranty template, ACL/company rule and sequence. Source findings only; no PDF rendering, declaration creation or Odoo integration tests executed.
