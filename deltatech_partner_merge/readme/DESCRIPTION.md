Merges partner records that share the same VAT number, in bulk.

Odoo's own merge wizard walks the foreign keys **group by group**: for every pair it goes through all
~158 columns that reference `res_partner`. Fine for a handful of duplicates; for thousands of groups
it means hundreds of thousands of statements and does not finish in any reasonable window.

This module inverts the loops — **one statement per column for the whole batch** — and keeps foreign
keys enabled throughout, so integrity is guaranteed by PostgreSQL rather than by the procedure being
right. On a production database of 538.000 partners, merging 5.350 records took about four and a half
minutes.

**Safety.** The simulation is not a flag you can forget: it runs the whole merge on a separate
transaction and rolls it back, so it cannot write even if something is wrong. Applying is a distinct
step, guarded by its own access group, and refuses to finish if any reference is left pointing at an
absorbed record.

**What it does not touch by itself.** Groups whose unreconciled balance is spread over several records
are classified apart — merging those moves money between ledgers and belongs with the accountant.
Also left out: groups holding your own company record, groups with portal users on more than one
record, and groups whose names differ completely on the same VAT number.

**Kept record.** Chosen by document volume — most invoices, then most sales orders, then oldest. Since
that is not the same as name quality, the surviving record is flagged when its name looks mangled at
import, with the names of the absorbed records alongside for correction.

The same procedure is available as plain SQL scripts in `deltatech/scripts/partner_merge/`, for when
it has to be run outside Odoo.
