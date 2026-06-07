Provides a set of scheduled maintenance actions (cron jobs) to keep an Odoo database clean and performant.
All jobs are **disabled by default** and run in **dry mode** (no data is changed until explicitly enabled by an administrator).

**Key features:**

- Delete duplicate XML (EDI/ANAF) attachments on invoices — cron: *Delete duplicate xml attachments*
- Delete old generated PDF attachments on invoices — cron: *Delete pdf invoice attachments*
- Delete old generated PDF attachments on sale orders — cron: *Delete pdf sale order attachments*
- Delete old generated PDF attachments on stock pickings — cron: *Delete pdf pickings attachments*
- Delete old chatter messages (with linked non-ANAF attachments) — cron: *Delete mail messages*
- Create missing stock reordering rules for storable products — cron: *Create missing reordering rules (0/0)*
- Merge duplicate contacts by e-mail address — cron: *Merge duplicate contacts by email*
- Merge duplicate companies by VAT number — cron: *Merge duplicate companies by VAT*
- Normalize company name suffixes (SRL → S.R.L., SA → S.A., etc.) — cron: *Normalize company names*
- Force-cancel a sale order together with all its pickings, stock moves and account moves via a server action
  (`force_cancel_order_and_moves`); the server action must be created manually for security reasons
