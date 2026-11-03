Adds sales-team tracking to analytic accounting and a tool to split analytic
amounts across several analytic accounts by percentage.

## Analytic distribution by sales team

**Sale team on distribution models.** The analytic distribution model gets a
*Sale team* field. On customer invoices, credit notes and sales receipts, the
product lines take the distribution of the model whose *Sale team* is the
invoice's sales team, when exactly one such model exists. The distribution is
recomputed when the sales team of the invoice changes.

**Sales team on analytic items.** Analytic items keep a sales team and the
product category of their product:

- from the sales team of the customer invoice, credit note or sales receipt;
- for journal entries of a stock transfer (when the stock and sales-stock
  modules are installed), from the sales team of the sale order of the transfer;
- on vendor bills and refunds, from the sales team whose name equals the name of
  the analytic account.

In **Accounting > Accounting > Transactions > Analytic Items** and
**Accounting > Reporting > Analytic Report**, the *Group By* menu offers
**Sale team** and **Product category**.

## Analytic split

**Analytic split templates.** A template lists analytic accounts with a
percentage each; the percentages must total 100.

**Analytic splits.** A split distributes either a fixed *Amount* or an existing
analytic item (type *Line*) according to a template:

- **Compute** fills the split lines from the template;
- **Confirm** creates one analytic item per split line, on the split date, and
  checks that the lines add up to the amount to split. For a *Line* split, the
  original analytic item is deleted and replaced by the new ones;
- **Reset** deletes the created analytic items and returns an *Amount* split to
  draft. A *Line* split cannot be reset.

## Configuration

- **Accounting > Configuration > Analytic Accounting > Analytic Distribution
  Models**: set the *Sale team* on the models used for sales.
- **Accounting > Configuration > Analytic Accounting > Analytic split templates**
  and **Analytic splits**.
- The split menus are visible to accounting administrators when the *Analytic
  Accounting* setting is enabled. Only users in the group *Analitic split user*
  (**Settings > Users & Companies > Groups**) may open templates and splits.

In Odoo Community the app is named **Invoicing** instead of **Accounting**.

## Limitations

- On vendor bills the sales team is found only by an exact match between the
  analytic account name and the sales team name.
- A split without a *Name* cannot be confirmed: the analytic items need a
  description.
