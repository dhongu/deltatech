# 19.0.1.0.1

- Fix: the module could not be installed together with `l10n_ro_invoice_report` (the invoice report line description is rebuilt there). The invoice line block is now added inside the description cell instead of after a fixed `span`.

# 19.0.1.0.0

- New module. Moves the weight, volume and net weight lines of the quotation report and the copy of these values to the variants out of `terrabit_electromax` (task #1601), and adds the same on the customer invoice. Quotations and invoices have their own option in the settings, and the copy to variants is optional.
