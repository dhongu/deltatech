## 19.0.1.0.1

- [FIX] the extra line is added again in the POS. Since 19.0 the point of sale
  builds a line from `vals.product_tmpl_id` and no longer from `vals.product_id`,
  so the patch read an undefined product and silently skipped the extra line -
  the SGR deposit product was never added to the receipt. The template is now
  read from either key, and the extra line is requested with the template as
  well, which 19.0 requires
