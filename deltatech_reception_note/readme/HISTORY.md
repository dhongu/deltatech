## 19.0.0.1.4 (2026-10-03)

- Fixed: confirming a reception note consumed sent RFQs of every allowed company, so a receipt in
  one company could reduce (and mark empty) the RFQ of another company. Only the sent RFQs of the
  reception note company are consumed now, in that company context (RECEPTION-002).
- Fixed: the "Create reception note" wizard created the RFQ-only counterpart in the active company
  and its default currency, while copying the prices and taxes of the source order unchanged. The
  new RFQ now keeps the company, currency and fiscal position of the source order (RECEPTION-004).
  The amounts of new RFQs created from foreign-currency orders change accordingly (same figures,
  now in the right currency).

## 19.0.0.1.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.0.1.2 (2026-07-29)

- The two errors raised when confirming a reception note now name the missing coverage as a *sent*
  RFQ and tell the user what to do about it: tick "Ignore quantities" to receive the goods anyway.
  Until now the message only stated that the product or the quantity was not found, leaving no clue
  that the field exists.
- Restored the Romanian translation of those two errors and of the chatter summary of forced
  quantities. All three had gone stale: the messages were reworked from `.format({})` to named
  `%`-placeholders without regenerating `i18n/ro.po`, so the `msgid` no longer matched and the
  translation was silently dropped — the user saw English text on a Romanian database.
