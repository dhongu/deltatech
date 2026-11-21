The module works right after installation. All internal users can keep the register;
nothing has to be configured for that.

## Access rights

| Who | Can |
|---|---|
| Any internal user | Read, create and edit records, reserve numbers, register, cancel, print the report |
| **Ledger / Manager** | Everything above, plus **delete** records and **reactivate** canceled records |
| Administration / Settings | Is a Ledger Manager automatically |

To make someone a manager: **Settings > Users & Companies > Users**, open the user and
set **Ledger** to **Manager**.

## Numbering

The numbers come from the sequence *Ledger Sequence* (code `ledger.ledger`), found in
**Settings > Technical > Sequences** (developer mode). It is a *no gap* sequence
with a subsequence per year and the prefix `%(year)s/`, size 5.

- To change the format, edit the prefix or the size of the sequence.
- To continue an existing paper register, open the date range of the year and set its
  **Next Number** (for example `121` if the last number used on paper is `120`).
  A new year gets its own range, starting at `00001`.

## Multi-company

Each record has a company, taken from the company active when it is created, and the
record rule shows a user only the records of the companies they are logged in to. The
sequence is shared by default. To have a separate numbering per company, create a
sequence with the same code `ledger.ledger`, the same settings (no gap, subsequences per
date range, prefix `%(year)s/`) and the company set; the sequence of the
current company is used.

## Links to other documents

The *Links* tab offers the models of the installed apps only (Project, Helpdesk, Sales,
Purchase, Accounting, Inventory). Nothing has to be configured.
