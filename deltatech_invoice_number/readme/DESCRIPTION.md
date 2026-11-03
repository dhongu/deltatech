Keeps customer invoices in chronological order on the journals where it
matters, and lets a dedicated group of users correct the number of an invoice.

**Chronological invoice dates.** On a sales journal with *Restrict invoice
date* enabled, a draft customer invoice or credit note cannot be confirmed with
an invoice date earlier than the latest posted document of the same type in that
journal. The error states the earliest date allowed. When the journal is chosen
on a draft invoice, a warning shows the same information.

**Change of the invoice number.** Users in the group *Allow to change invoice
number* get the action **Change invoice number** in the Actions menu (gear icon)
of the invoice form. The wizard proposes the current number; after **Apply**,
the new number is written on the invoice and copied to the reference of its
journal items (and to the invoice *Reference* for customer documents).

## Configuration

- **Accounting > Configuration > Journals**, a journal of type *Sales*, tab
  **Journal Entries**, section **Invoice numbering**: tick *Restrict invoice
  date*.
- **Settings > Users & Companies > Groups**: add the users who may change
  invoice numbers to the group *Allow to change invoice number*.

## Limitations

- The **Invoice numbering** section also shows a *Journal Sequence* field. The
  module contains a method that numbers a draft invoice from this sequence, but
  no button or menu calls it, so the field has no effect in the interface.
- The new number is written as typed: the wizard does not check it against the
  journal's numbering format or for gaps.
