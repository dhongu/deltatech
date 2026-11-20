## 19.0.1.0.1 (2026-11-20)

- Fix: the cost of the disassembled product is allocated on the actual cost during the validation
  (resulting moves, journal entry and line values), not on the estimate from the standard price.
- Fix: a validated or cancelled disassembly report and its lines can no longer be changed, nor reset
  to draft, by a direct write (RPC included); the state and the actual cost change only through the
  workflow buttons.

## 19.0.1.0.0 (2026-10-12)

- New module: disassembly report without a bill of materials. The disassembled product leaves the
  stock at its actual cost, which is split over the resulting products (by quantity, reference
  price, percentages or fixed values, rounding on the last line); losses within or above the norm;
  one journal entry per report, with the Romanian account correspondences by synthetic account
  (34x through 711, 371 → 30x and 30x → 30y only by company setting, other pairs refused);
  PDF report with the signatures of the committee.
