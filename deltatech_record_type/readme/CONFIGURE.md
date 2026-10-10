Install `deltatech_record_type` (it pulls in `sale`, `sale_stock` and `purchase`), then:

- **Settings → Sales → Quotations & Orders → Confirmed without record type**:
  - ticked: all internal users can confirm orders without a type;
  - cleared: only members of the group *Can confirm orders without order type* can do so.
    After installation only the administrator and the system user are in that group, so as soon
    as you define a type, all other users must pick one before confirming. Grant the group only
    to those who need the exception.
- Define the types you need (see *Usage*, Step 1). A document shows the type field only if at
  least one type exists for it.
- To use stock routes on a type, enable **Settings → Inventory → Multi-Step Routes**. The
  **Routes** field is visible only then.
