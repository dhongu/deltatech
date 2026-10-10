Leaves closed stock valuation layers out of the Romanian **storage sheet** (*fișa de magazie*, from
the `l10n_ro_stock_report` module of the Romanian localization): the valuation layers that no longer
matter can be archived, and the storage sheet can then be run on the active layers only.

- **Archivable valuation layers**: Stock valuation layers get an *Active* field, so they can be
  archived from *Inventory > Reporting > Valuation*; the valuation layers of a transfer still show the
  archived ones.
- **Only active option**: The storage sheet wizard gets an **Only active** option; when ticked, the
  initial balance, the receipts, the deliveries and the final balance leave out the archived layers.
- **More on the storage sheet lines**: The receipt and delivery lines of the storage sheet also store
  the operation type and the invoice date.

**Important:** an archived valuation layer is also left out of Odoo's own stock valuation (the value
and valued quantity of the products, the valuation report), not only of the storage sheet. Archive
layers only after checking the effect on the valuation of the products concerned.

**Data sent outside Odoo:** none.
