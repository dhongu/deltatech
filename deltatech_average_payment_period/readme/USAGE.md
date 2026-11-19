## Before you start

The report only counts invoices that are **fully reconciled** with their payment. Make sure the
payment methods of your bank journal have an account set (**Invoicing**, or **Accounting** on Enterprise, **→ Configuration → Journals →
Bank**, **Incoming Payments** and **Outgoing Payments** tabs): without it, a payment creates no journal entry, the invoice stays
**In Payment** and does not reach the report.

## 1. Pay an invoice in full

Open a posted customer invoice or vendor bill and click **Pay**. When the payment
covers the whole invoice, the receivable or payable line is reconciled with the payment and the
module stores the payment date and the number of days automatically.

![Customer invoice of Client Alfa SRL dated Aug 5 for 2,420.00, with 30 days payment terms, the Paid ribbon and the payment of 09/04/2026, 30 days after the invoice date](static/description/en/01_factura_platita.png)

- **Payment Days** = accounting date of the payment − accounting date of the invoice.
- If the invoice is paid in several instalments, the date of the payment that closes it is kept.
- If the reconciliation is removed (on the invoice, the ⓘ icon next to **Paid on …** → **Unreconcile**), the payment date and days are
  cleared and the invoice leaves the report; a new full reconciliation computes them again.

## 2. Read the report by partner

Go to **Invoicing** (or **Accounting** on Enterprise) **→ Reporting → Average Payment Period**. The pivot opens grouped by **Partner**:

- **Balance** — total of the paid invoices: positive for customers, negative for vendors (the grand
  total mixes both, filter customers or vendors to read it);
- **Payment Days** — average days to payment, **weighted by the invoice amount**;
- **Plain payment days** — simple average of the days, computed on customer invoices and vendor bills;
  a reconciled credit note counts with 0 days.

![Average Payment Period pivot grouped by partner with the Balance, Payment Days and Plain payment days columns](static/description/en/02_raport_pe_parteneri.png)

Example: an invoice of 1,210.00 paid in 10 days and one of 2,420.00 paid in 30 days give
**Payment Days** 23.33 and **Plain payment days** 20.00. Unpaid or partially paid invoices are not
included. Use the **Date** filter of the search bar to select the period, and **Download xlsx** to
export the table.

## 3. Break it down by month

In the same pivot, click the **Total** column header and choose **Date → Month**: each partner gets
one column per month, with the average days of the invoices of that month.

![Average Payment Period pivot with partners as rows and the invoice months as columns](static/description/en/03_raport_pe_luni.png)

## 4. Compare partners on a graph

Switch to the **Graph** view: it opens on the **Payment Days** measure, with one bar per partner
for its weighted average days to payment, the same values as in the pivot.

![Average Payment Period bar graph with one bar per partner for the Payment Days measure](static/description/en/04_grafic_zile_plata.png)
