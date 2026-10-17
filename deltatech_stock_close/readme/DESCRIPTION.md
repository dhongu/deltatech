Leaves closed stock moves out of the Romanian **storage sheet** (*fișa de magazie*, from the
`l10n_ro_stock_report` module of the Romanian localization): once a period or a fiscal year is closed,
the storage sheet can be run on the stock moves that are still open only.

- **Valuation Active flag**: Each stock move gets a **Valuation Active** flag, on by default; a move
  whose flag is off counts as closed. In Odoo 19 the valuation is kept on the stock move, so the flag
  is set there.
- **Only active option**: The storage sheet wizard gets an **Only active** option; when ticked, the
  initial balance, the receipts, the deliveries and the final balance leave out the closed moves.
- **Report unchanged otherwise**: With the option off, the storage sheet is exactly the one of the
  Romanian localization; the stock moves themselves are never hidden elsewhere in Odoo.

- **Close Stock Moves**: The *Inventory > Operations > Adjustments > Close Stock Moves* wizard closes
  every done stock move of the company dated on or before a chosen day. No accounting entry is changed.
- **Flag on the stock move list**: The **Valuation Active** column (hidden by default) and the
  **Closed** filter of the stock move list let a stock manager check or reopen a single move.

**Data sent outside Odoo:** none.
