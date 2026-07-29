## 19.0.0.1.2 (2026-07-29)

- The two errors raised when confirming a reception note now name the missing coverage as a *sent*
  RFQ and tell the user what to do about it: tick "Ignore quantities" to receive the goods anyway.
  Until now the message only stated that the product or the quantity was not found, leaving no clue
  that the field exists.
- Restored the Romanian translation of those two errors and of the chatter summary of forced
  quantities. All three had gone stale: the messages were reworked from `.format({})` to named
  `%`-placeholders without regenerating `i18n/ro.po`, so the `msgid` no longer matched and the
  translation was silently dropped — the user saw English text on a Romanian database.
