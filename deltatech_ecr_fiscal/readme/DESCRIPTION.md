Defines, in a single place, the fields that record the result of printing on a fiscal
cash register (ECR/AMEF):

- **Fiscal receipt (BF)** — receipt number within the current Z report; restarts at every Z
- **Fiscal document (NR)** — fiscal document number, unique per device; the one to use
  when a document must be identified without ambiguity
- **Z report** — number of the Z report the receipt belongs to
- **Fiscal state** — outcome reported by the device driver
- **Fiscal error** — error message, when the device refused or failed

The fields are added to **journal entries** here, and to **POS orders** by
`deltatech_pos`, through the abstract mixin `deltatech.ecr.fiscal.mixin`.

Written by the driver — the POS payment screen, or the store print action, after the
Terrabit Connect agent replies — and read by everything downstream: reports, fiscal
compliance modules, the Romanian localization.

The module depends on `account` alone — not on `point_of_sale` — so the contract can be
consumed from suites that have no access to the cash register driver modules, and from
the POS-free store alternative (`deltatech_sale_store`) without pulling in Point of Sale.
