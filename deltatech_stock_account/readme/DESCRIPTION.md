Small additions to stock valuation: the value of each transfer in the transfers
list, accounting settings passed from a product category to its subcategories,
and control over who may change the cost of a product that is in stock.

**Value of transfers.** Adds an **Amount** column to the transfers list
(for example *Inventory > Operations > Transfers > Receipts*), with the total at the bottom. The amount
is the sum of the valuation **Value** of the stock moves of the transfer; moves
that are not valued (for example internal transfers) count as zero.

**Accounts propagated to subcategories.** When the **Stock Account** of a product
category is changed, the category's accounting settings are copied to all its
subcategories: **Income Account**, **Expense Account**, **Stock Account**,
**Price Difference Account**, **Stock Journal**, **Costing Method** and
**Inventory Valuation**. The same copy can be run at any time with the
**Propagate Accounts** action on the category form (developer mode).

**Settings inherited from the parent category.** When you choose a **Parent
Category** on a category, the same accounting settings are copied from the
parent.

**Cost changes restricted.** Only users in the **Change Product Price** group can
change the **Cost** of a product that has quantity on hand. Other users get an
access error. The administrator is in the group by default.

## Configuration

Add users to the **Change Product Price** group in *Settings > Users & Companies
> Groups* (developer mode).

## Limitations

- The value of a transfer is shown only in the transfers list, not on the
  transfer form.
- The **Stock Variation Account** of the category is not propagated.
