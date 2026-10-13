Set this up once per company, ideally together with the customer: choosing the policy is a commercial decision, not a technical detail.

**Step 1 — Choose the policy**

Go to **Settings → Sales → Pricing → Selling below cost**. Pick one of:

- **Block the sale** (default): the price cannot be saved and the order cannot be confirmed below cost.
- **Warn only**: the line is flagged and the order can still be confirmed.
- **No check**: nothing is flagged or blocked.

**Step 2 — Set the margin limit (%)**

In the same place. **0** flags only negative margins; a negative value (for example -10) tolerates a loss up to that percentage; a positive value (for example 5) also flags thin margins that are still profitable.

**Step 3 — Optional: check on confirmation only**

On the **Block the sale** policy you can tick **Check margin on confirmation only**. Salespeople can then prepare a quotation freely, and the check runs when the order is confirmed.

![Selling below cost policy and margin limit in Settings → Sales → Pricing](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_margin/sale_margin_policy_settings.png)

**Step 4 — Repeat for every company**

The policy is stored per company. A newly created company starts on **Block the sale**.

**Step 5 — Check user groups**

- *Hide purchase price in sale order and customer invoice*: users without it do not see cost and margin. Keep regular salespeople out of this group.
- *Sell below the purchase price* and *Sell below margin limit*: members can go past the block (a note remains in the chatter).
- *No change price on sale order*: price and discount become read-only.

**Step 6 — Fill in the purchase cost on products**

Without a cost (or with cost 0) there is nothing to compare and no warning is shown.
