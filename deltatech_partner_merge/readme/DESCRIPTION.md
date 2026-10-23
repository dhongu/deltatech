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

**Finding duplicates beyond the VAT number.** *Partner Merge › Find Duplicates* looks for partners
that are probably the same record, typically individuals created twice by an import or an online
order, and leaves the decision to you, group by group. It does not change any partner.

- Exact matches on the VAT number (without the country prefix), the phone (E.164, so `0722 …` and
  `+40 722 …` meet), and the email (lowercase).
- Similar names (without diacritics or legal forms, words sorted) at the same street or postcode,
  or similar names alone if you choose so. Names are compared only inside a block (same city, or
  same first letters), so large databases are not compared all against all.
- Each group shows its score and the reason ("same phone +40722…", "name 92% + same street").
  *Merge* opens the standard Odoo merge wizard on the group, where you choose the record to keep.
  *Not duplicates* remembers the pair, so later scans skip it.
- Left out: partners of internal users and of your companies, a partner and its own contacts,
  invoice and delivery addresses of the same customer, partners of different companies, and values
  shared by too many partners (placeholders, switchboards), which are listed in the report.

The name comparison uses `rapidfuzz` when it is installed on the server. Without it, the scan falls
back to Python's `difflib`, which is slower and only compares blocks of up to 1,500 partners; the
larger blocks are listed in the report. `phonenumbers` and `unidecode` are used the same way, if
present. None of them is required.
