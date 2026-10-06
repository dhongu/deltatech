## 19.0.0.1.0 (2026-10-05)

- **Reservations:** new *Reserved* state and *Reserve a Number* menu. A reserved
  number has no date until it is chosen, between the dates of the previous and of
  the next number; the date must also be in the year of the number. A reservation
  is registered (*Register*) or canceled.
- **Numbering:** one common sequence for entries and exits, restarted every year,
  now *no gap*. The sequence is `noupdate`, so a migration converts the existing
  one: the range of the current year continues the existing numbers.
- **Cancellation** asks for a reason (wizard), kept on the record and in the chatter.
  The number stays in the register. A Ledger Manager can reactivate a canceled
  record.
- New group *Ledger / Manager* (implied by Administration / Settings): only it can
  delete records. Regular users keep read, write and create.
- **Links** tab: web links and links to a project, task, helpdesk ticket, sale or
  purchase order, invoice or transfer (only the apps installed are offered).
- Warning banner for a possible duplicate (same type, document number and contact).
- **PDF report** of the register for a period (*Print Ledger* menu, also available
  on selected records).
- Views: kanban by state, calendar, pivot and graph; canceled ribbon, type badge,
  optional columns, search by contact, date filters and grouping. Removed the
  deprecated `statusbar_colors`. The list shows all the numbers by default,
  canceled ones included.
- Chatter and tracking (`mail.thread`, activities); multi-company (`company_id`,
  record rule).
- The record date is required for active records and prefilled with today.
  Duplicating a record gives it a new number and the *Active* state.
- Manifest: category, summary, *Beta*.

## 19.0.0.0.3 (2026-09-30)

- New module icon: a register with the entry and exit arrows, in the flat style of the other modules; it replaces the old gradient one.

## 19.0.0.0.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
