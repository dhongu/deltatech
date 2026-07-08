- No configuration is needed for the default behavior: once installed,
  saving a product (template or variant) with an **Internal Reference**
  (`default_code`) or **Barcode** that is already used by another
  product — including archived ones — raises a validation error listing
  the conflicting product(s).
- To let specific users bypass this restriction (e.g. to temporarily
  reuse a code), add them to the **Allow duplicate product codes**
  security group: Settings > Users & Companies > Users > Access Rights.
  This group is hidden from the normal group list and only assigned to
  admin users by default.
