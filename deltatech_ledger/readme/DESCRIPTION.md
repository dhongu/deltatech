Register of incoming and outgoing documents (a "registru de intrări-ieșiri"). Every
document that enters or leaves the company gets one numbered record, so the register can
be shown to an auditor, printed for a period and searched at any time.

The numbering is one common series for entries and exits, restarted every year
(`2026/00001`) and without gaps: a number is never skipped, and a wrong record is
canceled instead of deleted, so its number stays in the register.

Features:

- One record per document, typed as **Entry** or **Exit**, with document number, date,
  contact, place of origin and a short description.
- **Reservations:** a number can be reserved in advance and dated later, between the
  dates of the previous and of the next number, so the register stays in
  chronological order.
- **Cancellation** with a mandatory reason; the number stays in the register. Only a
  Ledger Manager can reactivate a canceled record or delete records.
- **Links:** attachments in the chatter, web links, and links to a project, task,
  helpdesk ticket, sale or purchase order, invoice or transfer.
- Chatter and activities on every record, with tracking of the state, type, date,
  document number and contact.
- Warning when a document with the same type, number and contact is already registered.
- Views: list, kanban by state, calendar, pivot and graph (entries vs. exits per month).
- **PDF report** of the register for a period, or for a selection of records.
- Multi-company aware: each record belongs to a company and is visible only in it.

Scope & limitations:

- The module keeps a register of document references. It does not store the documents
  themselves (use the chatter attachments or the links for that) and it does not post
  any accounting entry.
- The number is always taken from the year of the day it is created, and the record
  date must be in the same year. A document dated in December cannot be registered in
  January; reserve its number in December instead.
- Dates must not decrease with the number, for active records as well as for
  reservations. A document with an earlier date than the previous number is registered
  by reserving the number first and dating it afterwards, within the allowed interval.
- Entries and exits share one numbering. Separate series per type are not supported.
- Because the series has no gaps, two users creating a record at the very same moment
  can get a "could not obtain lock" error; the second one only has to save again.
