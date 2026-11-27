# 20.0.1.1.0

- New: the estimated gross weight of the line in the list of lines of the quotation / sales order and of the customer invoice (optional column, hidden by default: enable it from the column selector).
- New: setting **Only the gross weight**, per company. On the printed quotation, sales order and invoice only the gross weight is shown (per line and in total), without the net weight and the volume.

# 20.0.1.0.1

- Fix: the module could not be installed together with `l10n_ro_invoice_report` (the invoice report line description is rebuilt there). The invoice line block is now added inside the description cell instead of after a fixed `span`.

# 20.0.1.0.0

- Migration to 20.0 from 19.0. The quotation and invoice reports anchor on the new `label` field of the line, and the option is read with the typed `ir.config_parameter` API of Odoo 20 (`get_bool`).
- Odoo 20 already writes the weight and the volume of a template on all its variants, so "Copy weights to all variants" now adds only the net weight and the variants created on demand; tests and texts adjusted.

# 19.0.1.0.0

- New module. Moves the weight, volume and net weight lines of the quotation report and the copy of these values to the variants out of `terrabit_electromax` (task #1601), and adds the same on the customer invoice. Quotations and invoices have their own option in the settings, and the copy to variants is optional.
