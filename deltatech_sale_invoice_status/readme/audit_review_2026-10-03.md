# Integrated source review — 2026-10-03

Entire eligible source read. The _can_be_invoiced_alone override composes with native delivery exclusion and sale discount-product exclusion. Native sale.order._compute_invoice_status only consults the hook when another line has status no; all-service invoiceable orders retain to invoice, matching module description. Native _get_invoiceable_lines uses quantities independently; the module changes the status indicator rather than prohibiting explicit invoice creation. No new confirmed defect. No database invoicing/browser tests executed.
