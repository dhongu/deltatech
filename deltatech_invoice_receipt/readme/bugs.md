# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## RECEIPT-001 — P1: Automatic receipt deletes moves that already have a quantity

- **Status:** Open.
- **Location:** `models/purchase.py`, `receipt_to_stock()`, lines 36–40.
- **Trigger:** Run automatic receipt on an assigned picking whose stock moves already have a reserved or entered quantity.
- **Actual behavior:** The method only keeps moves with a positive demand and zero `quantity`. Every other move is unlinked, including a legitimate move with demand 5 and quantity 5.
- **Example:** Isolated execution deleted a 5-unit assigned move before calling picking validation.
- **Impact:** Expected receipt lines can disappear, so products are not received as intended.
- **Evidence:** Executed the existing method with a mocked assigned picking. In Odoo 19, move quantity is computed from stock move line quantities, including assigned quantities. The current module test does not assert the resulting stock quantity.
- **Suggested fix:** Retain valid positive-demand moves, preserve or deliberately adjust existing quantities, and handle zero-demand lines separately.
- **Validation needed:** Automatic receipt with zero, fully reserved, partially entered, and fully entered quantities; assert actual received stock.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
