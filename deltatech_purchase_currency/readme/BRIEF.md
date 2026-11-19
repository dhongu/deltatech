# Brief: deltatech_purchase_currency

## Request

> „pt maxima trebuie sa mai facem functioalitate prin care comanda de vanzare se face in EUR si
> factura in RON (stiu avem un modul) — e posibil sa fie necesar sa facem la fel si pt achzitiile
> din romanaia dar preturile sa fie in EUR”
>
> Follow-up: „in functie de jurnalul de facturare, de pus jurnalul in comanda la fel ca la
> comanda de vanzare” (2026-11-19)
>
> Version 20.0.1.1.0: „si daca furnizorul factureaza la un alt curs cum se poate specifica cursul
> in factura” (2026-11-19)
>
> Version 20.0.1.2.0: „nu se poate afisa cursul valutar de la BNR in loc de zero ? dupa schimbarea
> datei se aduca cursul valutar de la BNR si se afiseaza o notificare ca a fost modificat (asta pt
> cazul in care userul introduse cusrul si apoi data si cursul este uprascris cu cel de la BNR)”
> (2026-11-19)

## Purpose

Romanian suppliers often quote and confirm purchase orders in EUR but issue the vendor bill in
RON, at the exchange rate of the bill date. Standard Odoo bills a purchase order in the order
currency, so the buyer has to retype every price in RON. With this module the purchase order
carries an invoicing journal, as the sales order does with `deltatech_sale_currency`; the bill
takes the journal currency and the order prices are converted at the bill date rate.

## Who operates it

The purchase user picks the invoicing journal on the order (group *Purchase / User*); the
accountant creates and checks the vendor bill (group *Invoicing*).

## Scope

- Suite and technical name: `deltatech` / `deltatech_purchase_currency`
- New module, purchase counterpart of `deltatech_sale_currency`
- `depends`: `purchase` (purchase order, vendor bill from order, purchase line on bill line);
  `account` comes with it
- New models: none
- Extended standard models:
  - `purchase.order`: `journal_id` (Invoicing Journal, purchase journals of the company)
  - `purchase.order.line`: conversion of the unit price to the bill currency, one overridable
    method
  - `account.move`: price recomputed on bill date / currency change
  - `account.move.line`: the price matching flag compares in the bill currency

## Flow

1. The buyer creates a purchase order for a Romanian supplier, in EUR.
2. On the *Other Info* tab they set *Invoicing Journal* to a purchase journal without currency
   (the RON vendor bills journal).
3. They confirm the order; the goods are received.
4. *Create Bills* (purchase order list, order selected) or *Upload Bill* (order form, with the
   supplier PDF) — Odoo 20 has no *Create Bill* button on the order form: the bill is in RON, on
   that journal, with the EUR prices converted at today's rate (in Odoo 20, the last rate dated
   before today).
5. The accountant sets the *Bill Date* from the supplier invoice: the prices are converted
   again, at the rate of that date.
6. *Vendor Rate* shows the Odoo (BNR) rate of the bill date, as bill currency for 1 unit of the
   order currency (e.g. 5.0912 RON for 1 EUR). When the supplier invoice states another rate,
   the accountant types it there, after the bill date: the prices are converted at that rate.
   A later bill date change brings the BNR rate of the new date back and says so.

## Acceptance criteria

- **CA1:** EUR purchase order with *Invoicing Journal* = a journal without currency → *Create
  Bills* → the bill is in the company currency, on that journal, and the unit price is the EUR
  price converted at today's rate.
- **CA2:** On that draft bill, setting *Bill Date* to an earlier date → the unit price becomes
  the EUR price converted at the rate of that date.
- **CA3:** EUR purchase order without *Invoicing Journal* → the bill stays in EUR with the order
  price (standard behaviour, foreign suppliers unaffected; the journal is the one standard Odoo
  picks for the currency).
- **CA4:** EUR purchase order with *Invoicing Journal* = a journal in EUR → the bill is in EUR,
  on that journal, with the order price.
- **CA5:** The bill line in another unit of measure than the order line (Dozens vs Units) →
  after the bill date changes, the price is the order price brought to the bill line unit, then
  converted (10 EUR/Unit → 120 EUR/Dozen → converted).
- **CA6:** On a converted bill, the purchase matching flag of the line shows no price
  difference; after the price is changed by hand it shows the difference.
- **CA7:** A new vendor bill to which the order is added via *Auto-Complete* → the bill takes
  the order invoicing journal and currency, with converted prices.
- **CA8:** On a RON bill of a EUR order, *Vendor Rate* is shown in the bill header, under the bill dates; on a
  bill in the order currency, or with lines from orders in different currencies, it is hidden.
- **CA9:** Setting *Vendor Rate* = 5.10 → the unit price becomes the EUR price × 5.10 (in the
  bill line unit).
- **CA10:** Changing the bill date sets *Vendor Rate* to the Odoo rate of the new date and
  converts the prices at it; clearing *Vendor Rate* puts the Odoo rate of the bill date back.
- **CA11:** With *Vendor Rate* set, the matching flag compares with the order price at that
  rate (no difference shown on unchanged lines).
- **CA12:** A negative *Vendor Rate* is refused with an error on save.
- **CA13:** A RON bill created from a EUR order shows in *Vendor Rate* the Odoo rate of the bill
  date (not 0), and the prices match it.
- **CA14:** *Vendor Rate* typed by hand, then the bill date changed → the rate is replaced by the
  Odoo rate of the new date and a warning names the replaced rate and the new one; when the
  rate was not typed by hand, the date change shows no warning.

## Edge cases

- Multi-company: `journal_id` is restricted to the purchase journals of the order company
  (`check_company`).
- Bill with a manual price change, then a new bill date → the price is reset from the order,
  as in `deltatech_sale_currency` (the bill date drives the rate).
- Bill date change on a bill in the same currency as the order → prices are left untouched
  (manual corrections on EUR bills are kept).
- Several orders on one bill: native grouping is by partner and bill currency, not by journal,
  so orders with different journals but the same bill currency end up on one bill, in the journal
  of the first order (documented; bill them one by one to keep the journals apart).

## Decisions taken

| Decision | Choice | Reason |
|---|---|---|
| Which currency the bill gets | `journal_id.currency_id` or the company currency; no journal → order currency | User's choice: journal on the order, as on the sales order; empty journal keeps the standard behaviour for foreign suppliers |
| Journal field visibility | visible on *Other Info* for all purchase users (not debug-only as on sales) | The buyer has to set it for every RON-invoiced order |
| Rate used | Odoo currency rate (BNR provider) at the bill date, today when unset | Same as `deltatech_sale_currency` |
| BNR + percentage (Maxima FR1) | not in this module; one method `purchase.order.line._get_invoice_price_unit()` that `maxima_purchase` extends | User's choice |
| Price | free (no `price` key), like the pair module | User's choice |
| Vendor rate direction | bill currency per 1 unit of order currency (RON per EUR) | That is how a Romanian vendor invoice states it; the inverse Odoo rate would confuse the accountant |
| Vendor rate scope | one field per bill, only when all order lines come from one other currency | A single rate cannot serve two source currencies |
| Vendor rate vs bill date | the bill date resets the rate to the Odoo rate, with a warning when a typed rate is replaced | User's choice (v1.2): the field always shows a real rate; the accountant types the vendor rate after the date |
| How a typed rate is recognised | a hidden *Odoo Rate* field keeps the last rate filled in automatically; a different *Vendor Rate* is a typed one | No guess from the dates; works before the bill is saved |
| Vendor rate on the bill, not on the order | bill field, empty by default | The rate is known only when the invoice arrives |
| Matching flag | converted PO price compared in the bill currency | Otherwise every converted line is flagged as a price difference |

## Open decisions

None.

## Out of scope

- A default invoicing journal per supplier (proposal for a next version).
- Percentage above the BNR rate (`maxima_purchase`, FR1).
- Valuation differences between the receipt rate and the bill rate: they follow the standard
  stock accounting.
- Changing the price on the purchase order after the bill.
