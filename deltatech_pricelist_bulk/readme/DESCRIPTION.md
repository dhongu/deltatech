Adds rules to a pricelist for many products at once and applies the same price
computation to many existing rules, instead of entering the rules one by one.

**Add rules for many products.** The **Add Rules** button on the pricelist form, and the
**Add to Pricelist** action on the selected products (list or kanban of products or
product variants), open a wizard where you:

- choose what the rules apply on: **Products**, **Product Variants** or **Product Categories**;
- pick the products, or fill the list with all the products of some categories and of their
  subcategories (**Add Products of Categories**);
- set once the **Min. Quantity**, the **Validity Period** and the price computation, with the
  same options as a standard rule: **Fixed Price**, **Discount** (optionally on another
  pricelist) or **Formula** (based on the sales price, the cost or another pricelist, with
  discount or markup, rounding, extra fee and margins);
- choose what happens when the pricelist already has a rule for the same product, minimum
  quantity and validity period: keep it, update it or add a new rule.

One rule is created for each product, variant or category. At the end, a message shows how
many rules were added, updated or kept, and the resulting rules open in a list.

**Apply the same formula to many rules.** The **Apply Formula** button on the pricelist form
(all the rules of the pricelist) and the **Apply Formula** action on the selected rules of a
rules list change, on all the rules at once:

- the price computation; the values of the other price types are cleared, as on the
  standard rule form;
- and/or the minimum quantity;
- and/or the validity period.
