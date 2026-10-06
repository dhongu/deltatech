# Bug review — Generic Partner

Review date: 2026-10-02. Target version: Odoo 19.

No new confirmed defects in this complete eligible source review. This is not a guarantee of runtime correctness.

## Reviewed behavior

- Company-specific customer invoice/refund checks cover invoice and shipping commercial partners before superclass posting.
- Generic partner protection applies server-side to write/unlink, with editor/superuser exemptions and documented technical-field exceptions.
- Company create/write/unlink clears the cached protected-partner set for the relevant configuration changes.
- Journal restriction is documented as filtering proposed payment journals; it was not treated as an unconditional prohibition on direct accounting writes.
- Migration transfers selected legacy XML identifiers conditionally; source was reviewed but the migration was not executed.

## Review limitations

All eligible Python/XML source, including the migration, was read. No Odoo invoice/payment/access tests, database upgrades or browser tests executed. Runtime behavior and concurrent cache invalidation remain unverified.
