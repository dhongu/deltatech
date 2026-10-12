## 19.0.1.2.0 (2026-10-09)

**Fix** — scheduling an activity on a sale order no longer fails when
`deltatech_website_sale_status` is not installed: the order stage is copied
into the journal only when the field exists (ACTIVITY-001).

**Fix** — the activity journal follows the access scope of sale orders
(ACTIVITY-002):

- salespeople see only the journal of their own orders (or unassigned ones),
  "All Documents" salespeople and managers see all, always limited to the
  allowed companies;
- salespeople can only read the journal; only the Sales Administrator can
  edit or delete entries; internal users without sales rights have no access;
- entries keep being written automatically, by the system, for every user.

## 19.0.1.1.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.1.1 (2026-08-24)

**Fix** — logging no longer fails when an order line that is not saved yet
is deleted from the form.

The web client refers to unsaved lines through virtual ids (`virtual_7149`).
The description of the commands on `order_line` read this id as if it were one from
the database, and the operation ended with `Expected singleton` — the log of the
whole write was lost, including the legitimate changes made at the same
time, and a traceback was left in the log at every save of this kind.

Now the ids that are not numeric are displayed as text, and a line deleted
in the meantime is reported by id, without being read from the database anymore.

## 19.0.1.1.0 (2026-08-15)

**Fix** — the activity log no longer stores the content of binary fields.

Changing a binary field of the order (the AWB label, the signature) wrote into
`activity_log` the whole base64 content of the file. The same problem
inflated a customer's database by 1.7 GB through the equivalent module for transfers;
here the measure is preventive — at the current scale the order log stays small,
but `sale.order` has the same binary fields.

Now:

- binary fields are ignored completely when logging — they are no longer even
  read from the filestore, so writing on the order is even faster;
- the logged field values are truncated to 200 characters (2000 for
  x2many fields, described line by line), with the number of
  truncated characters marked;
- the chatter messages are truncated to 2000 characters;
- the log of one day is capped at 64 kB, keeping the recent activity.
