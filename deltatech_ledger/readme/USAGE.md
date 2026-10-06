## Opening the register

Open the **Ledger** app. The menu has three entries:

- **Records** - the register: all the numbers, canceled ones included (shown muted),
  newest first.
- **Reserve a Number** - opens a new record already in the *Reserved* state.
- **Print Ledger** - the PDF report of the register for a period.

## The life of a record

A record has one of three states:

| State | Meaning | Has a date? |
|---|---|---|
| **Reserved** | The number is kept for a document that is not ready yet | Optional, can be set later |
| **Active** | The document is registered | Required |
| **Canceled** | The record is void; the number stays in the register | Kept as it was |

```
Reserve a Number --> Reserved --Register--> Active
                        |                      |
                        +-------Cancel---------+--> Canceled --Reactivate (manager)--> Active / Reserved
```

## Registering a document

1. Go to **Records** and click **New**.
2. Choose the **Record Type**: *Entry* for a document received, *Exit* for a document sent.
3. Check the **Record Date** (today by default) and fill in the **Document Number** (the
   number written on the document), the **Contact**, the **Place of Origin** and, on the
   *Description* tab, a short description.
4. Save. The record gets its number (`2026/00123`) and is *Active*.

The record stays editable afterwards, and every change of the type, date, document number
or contact is logged in the chatter. A canceled record is read-only.

If a record with the same type, document number and contact already exists, a yellow
banner warns about a possible duplicate. The record can still be saved.

## Reserving a number

Use a reservation when a number must be kept for a document that is not issued yet, or
when a document has to be dated in the past.

1. Open **Reserve a Number**, choose the **Record Type** and save. The number is taken
   from the sequence now; the date stays empty.
2. A blue banner shows the interval in which the number can be dated: from the date of
   the previous number to the date of the next one. Numbers without a date are skipped
   when the interval is computed.
3. When the document is issued, set the **Record Date** inside that interval and fill in
   the document details.
4. Click **Register**. The record becomes *Active*. The button refuses to work while the
   date is empty.

What the date is checked against, on every save:

- it must be in the same year as the number (`2026/...` only accepts dates in 2026);
- it cannot be earlier than the date of the previous dated number;
- it cannot be later than the date of the next dated number.

The same rules apply to active records, so the register is always in chronological order.
The bounds themselves are allowed (several documents can have the same date).

## Canceling a record

1. Open the record (a reservation or an active record) and click **Cancel**.
2. Write the **reason** in the window that opens and click **Cancel Records**.

The record becomes *Canceled*, a red ribbon appears, the reason is shown on the form and
posted in the chatter, and the number stays in the register.

A canceled number is never reused. To see only the canceled records, use the
**Canceled** filter.

A **Ledger Manager** sees a **Reactivate** button on a canceled record. It brings the
record back to *Active* (or to *Reserved* if it has no date) and clears the reason.
Regular users cannot reactivate.

## Deleting

Regular users cannot delete records: cancel them instead, so the numbering has no hole.
Only a Ledger Manager can delete, and should do it only for test data.

## Attachments and links

- **Files:** use the paperclip in the chatter at the bottom of the record to attach the
  scan or the file of the document.
- **Links:** open the **Links** tab and add a line for each link.
  - *Odoo Record* - choose the document type (Project, Task, Helpdesk ticket, Sales
    order, Purchase order, Invoice, Transfer) and the record. Use it to tie the
    numbered document to the ticket or project it belongs to.
  - *Web Link* - paste an address (a shared folder, a web page...).
  - The **Label** is filled in automatically (the name of the record or the address);
    type another text to replace it.

## Searching and viewing the register

Use the search box to find a record by number, document number, contact, place of origin,
description or date. The filters are **Reserved**, **Active**, **Canceled**, **Entry**,
**Exit** and **Date** (month, quarter, year). The groupings are **Record Type**,
**Contact**, **Record Date** (by month) and **State**.

The icons at the top right change the view:

| View | Use |
|---|---|
| List | The register itself; the columns can be chosen from the selector at the end of the header |
| Kanban | Records grouped by state: what is reserved, active, canceled |
| Calendar | Records on their date, coloured by type; undated reservations are not shown |
| Pivot | Counts by month and type, to export or drill down |
| Graph | Entries versus exits per month |

## Printing the register

1. Open **Print Ledger**.
2. Choose the period (**From**, **To**; the current year until today by default) and,
   optionally, the **Record Type**.
3. Leave **Include Canceled** on to show the canceled numbers with their reason; this
   is what an auditor expects, as the series shows no gap. Switch it off for a clean
   list.
4. **Include Undated Reservations** adds the reserved numbers that have no date yet,
   for the years of the period.
5. Click **Print**. The PDF lists the records in order of their number, in landscape.

To print only some records, select them in the list and choose **Print > Ledger**.

## Typical cases

**A document arrives and is registered at once.** Records > New, Entry, fill in, Save.

**A letter is being prepared and must carry a number now.** Reserve a Number (Exit), put
the number on the letter, and when it is sent set the date and click Register.

**A document has an earlier date than the last registered one.** The register does not
accept it directly, because the dates cannot decrease with the number. If a number was
reserved for it, date that reservation inside its interval. Otherwise register it with
today's date and write the real date of the document in the description.

**A record was entered by mistake.** Cancel it with the reason. Do not delete it.

**The year changes.** Nothing to do: the first record of January gets `YYYY/00001`.
Records of the old year stay as they are and can still be edited, within their year.
