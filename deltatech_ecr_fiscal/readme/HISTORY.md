## 19.0.1.0.4 (2026-11-07)

- New field **Simulated receipt** (`fiscal_simulated`): set by the cash register drivers
  (`deltatech_pos` 19.0.2.16.1, `deltatech_sale_store` 19.0.2.6.1) when the receipt came from a simulated
  register, and read by `l10n_ro_pos_fiscal_compliance_ecr` 19.0.1.3.1, which keeps it out of the Z report
  and of the AMEF journal.
- Consultant sheet (`readme/FISA_CONSULTANT.md`) with the exported fields as screenshot, usage notes on
  simulated receipts, Romanian translation.

## 19.0.1.0.3

- Apps Store page: Usage and the context section in English (they were in Romanian), the
  Romanian translation in its own tab (`readme/*.ro.md`), and an own banner (the cover
  showed the banner of the `deltatech` module). Support address `support@terrabit.ro`.

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
