Restricts the use of the generic partner in accounting.

- Selected bank and cash journals are hidden when registering a payment for the
  generic partner configured on the current company.
- Customer invoices and credit notes issued to the generic partner cannot be
  validated: validation is refused with an explicit error, so the real customer
  has to be set first. Drafts stay allowed, so the flows that go through the
  generic partner (POS, e-commerce, imports) keep working. Vendor bills and
  journal entries are not affected.
