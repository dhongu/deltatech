## Viewing the Average Payment Period report

1. Open **Accounting** and navigate to **Reporting > Average Payment Period**.
2. The pivot view opens pre-grouped by **Partner**, showing for each partner:
   - **Balance** — total reconciled amount.
   - **Payment Days** — weighted-average days to payment across all reconciled lines.
   - **Plain payment days** — average days for customer invoices and vendor bills only (credit notes excluded).
3. Use the **search bar** to filter by partner name, reference, or date range. The **Date** filter supports month/quarter/year buckets.
4. Switch to the **Graph** view for a visual comparison across partners or time periods.
5. Add or remove groupings (e.g. **Date**, **Journal**) via the **Group By** menu to break down the average by period or by journal type.

## How Payment Days are populated

Payment Days are computed automatically whenever a journal entry line is fully reconciled:

- The module looks at the `full_reconcile_id` of each `account.move.line` and finds the date of the matching counter line (credit side for debit lines and vice versa).
- This date is stored as **Payment Date** on the journal entry line (visible in the Journal Items form under the **Due Date** field group).
- The difference `payment_date - invoice_date` (in days) is stored as **Payment Days**.

No manual action is required; values update automatically on reconciliation and de-reconciliation.
