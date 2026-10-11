## 20.0.1.0.0 (2026-10-12)

- Migration to Odoo 20: the time zone of the holidays is the company's (the
  working schedule no longer has one), the global time off is filtered on
  `count_as` (was `time_type`) and `zoneinfo` replaces `pytz`.

## 19.0.1.0.0 (2026-10-12)

- First version: payment term lines counted in calendar or working days, and the
  option to move a due date that falls on a non-working day to the next working
  day. The working days come from the company's working schedule and its public
  holidays. The payment term form warns when a working-day line may exceed 60
  calendar days.
