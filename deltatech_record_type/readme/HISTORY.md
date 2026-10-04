## 20.0.1.1.15 (2026-10-04)

- TYPE-001 (security): the default values of a record type (`record.type.default.values`) had no company rule, so a user of company A could read, change or delete the default values of a company-B record type (applied afterwards on that company's sales, purchases and invoices). The default values now follow the company of their record type (values of shared record types stay visible to everybody), and moving a default value to another record type requires write access on the target type.
- Port of 19.0.1.1.18 (dhongu/deltatech#3116). In 20 the company rule is a global row (no group, `crud`) of `security/ir.access.csv` instead of an `ir.rule` in `security/record_type_security.xml`.

## 20.0.1.1.14 (2026-10-01)

- Quotations without an order type accepted/signed or paid by the customer in the portal are confirmed again:
  the order type check applies only to internal users, not to portal/public users or to the confirmation made
  by an online payment.

## 20.0.1.1.13 (2026-09-29)

- Own module icon, instead of the generic gears it had.
