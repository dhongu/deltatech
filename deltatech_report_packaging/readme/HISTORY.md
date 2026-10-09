## 19.0.1.3.4 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.3.3 (2026-10-09)

- The product form no longer lists the materials of the category: they are configured and shown only on the category form, and the product form says in one line that it uses them while it has none of its own. Ticking "No packaging material" now hides the product's own materials list as well, so no table is left on the form.

## 19.0.1.3.2 (2026-10-03)

- PACKMAT-003 (security): the invoice packaging lines (`packaging.invoice.material`) had no company rule and any internal user could create, change or delete them on any invoice, also on invoices of other companies or without write access on the invoice (passing the `packaging_material_sync` context skipped even the invoice update). The lines now follow the company of their invoice through a multi-company record rule, and creating, changing or deleting a line requires write access on its invoice, whatever the context. Internal users without invoicing rights can no longer edit the packaging quantities of an invoice.

## 19.0.1.3.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
