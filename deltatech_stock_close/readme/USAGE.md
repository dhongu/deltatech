1. Close the stock moves of the closed period: *Inventory > Operations > Adjustments > Close Stock
   Moves*. In **Close until**, choose the last day of the closed period and press **Close**. Every done
   stock move of the company dated on or before that day (inclusive) is closed; no accounting entry is
   changed.

   ![Moves Analysis with three done receipts and, over it, the Close Stock Moves window: Close until (1) is Dec 31, 2025 and the Close button (2)](static/description/en/01_inchidere_miscari_asistent.png)

2. Check the closed moves in *Inventory > Reporting > Moves Analysis*: show the optional
   **Valuation Active** column (it is hidden by default) or use the **Closed** filter. To reopen a move,
   switch its **Valuation Active** toggle back on.

   ![Moves Analysis with the Valuation Active column, highlighted: the receipt of Jan 15 is still active, the receipts of Dec 12 and Nov 18, 2025 are closed](static/description/en/02_miscari_evaluare_activa.png)

3. Open the storage sheet of the Romanian localization (*Inventory > Reporting > Romanian Stock Sheet Report*).
   Tick **Only Active** to leave the closed stock moves out; leave it unticked for the full report.

   ![The Stock Sheet Report window: Location WH/Stock, the product, Date Dec 1, 2025 to Jan 31, Only Active ticked (1) and the Show Sheet button (2)](static/description/en/03_fisa_magazie_doar_active.png)

4. Run the report as usual (**Show Sheet**, or **Show Sheet Pdf**). With **Only Active**, the initial
   balance, the receipts, the deliveries and the final balance leave out the closed moves, so the
   initial balance built by closed moves is gone too.

   ![The storage sheet with Only Active, in list view: only the receipt of Jan 15 (30.00, 600.00) and the FINAL line with 30.00 and 600.00; there is no INITIAL line and the initial columns are 0.00](static/description/en/04_fisa_magazie_rezultat_active.png)

   The same sheet without the option is the storage sheet of the Romanian localization, with every
   move: the full stock and the figures that match the stock account.

   ![The storage sheet without the option: the INITIAL line with 40.00 and 800.00, the receipts of Dec 12, 2025 and Jan 15, and the FINAL line with 95.00 and 1,900.00](static/description/en/05_fisa_magazie_completa.png)
