## 19.0.1.1.1 (2026-08-24)

**Fix** — logging no longer fails when an operation that is not saved yet is
deleted from the transfer form.

The web client refers to unsaved lines through virtual ids (`virtual_7149`).
The description of the commands on the x2many fields read this id as if it were one
from the database, and the operation ended with `Expected singleton` — the log of the
whole write was lost, including the legitimate changes made at the same
time. The defect was reported on the equivalent module for sale orders,
which had exactly the same code.

Now the ids that are not numeric are displayed as text, and a line deleted
in the meantime is reported by id, without being read from the database anymore.

## 19.0.1.1.0 (2026-08-15)

**Fix** — the activity log no longer stores the content of binary fields.

Changing a binary field on the transfer (the AWB label, the signature) wrote into
`activity_log` the whole base64 content of the file. On a production
instance this meant an average of 32 kB per record, with peaks of 1.7 MB,
and about 1.7 GB in the database with only two months of activity kept.

Now:

- binary fields are ignored completely when logging — they are no longer even
  read from the filestore, so writing on the transfer is even faster;
- the logged field values are truncated to 200 characters (2000 for
  x2many fields, described line by line), with the number of
  truncated characters marked;
- the chatter messages are truncated to 2000 characters;
- the log of one day is capped at 64 kB, keeping the recent activity.
