## 19.0.1.0.4 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.3 (2026-10-03)

- MERGE-001 (security): the analysis read the partners of all companies and grouped them by VAT alone, and *Apply* rewrote and deleted them without any company or access check, so an operator limited to one company could merge or delete partners of other companies, and partners kept separately per company were merged into a partner of another company. Now:
  - a group is (VAT, company): partners of different companies are never merged together; the batch lines show the company;
  - the analysis only takes the partners of the selected companies; shared partners (no company) are taken only for system administrators and users with access to every company;
  - *Apply* refuses a batch with partners outside the user's companies or groups mixing companies, and requires write access (and delete access, unless *Archive instead of delete*) on the partners.
- Behavior change: operators without access to every company no longer see groups of shared partners, and same-VAT partners of different companies are no longer proposed for merging. The SQL scripts in `deltatech/scripts/partner_merge/` are unchanged (database-wide, run by the DBA).

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.1 (2026-09-23)

- The merge simulation rolls back its savepoint through `contextlib.suppress(_Rollback)`
  instead of `except _Rollback: pass`; behavior is unchanged.

## 19.0.1.0.0 (2026-08-18)

- Add: bulk merge of partners duplicated on the same VAT number, with classification, guards,
  simulation on a rolled-back transaction, and verification against a snapshot taken before the
  merge. Wraps the SQL procedure from `deltatech/scripts/partner_merge/`, validated on a client's
  staging database (575 records merged in three batches, zero discrepancies on invoices, orders,
  deliveries and unreconciled balance).
