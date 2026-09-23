Type whatever identifies the goods into any product field — a sales order line, a
purchase order line, a stock move, a search view.

- `gala` → every variant carrying the value *Gala Mast*, across all templates that use it.
- `apples gala` → only the apple variants, the pears are dropped.
- `apples gala 80` → the single variant that is also size *80/85 mm*.
- `GALA-13` → still matches the internal reference first, exactly as before.

The words can come in any order and a prefix is enough: `ga` matches *Gala Mast*. Words
are ANDed, so adding one always narrows the result, never widens it.
