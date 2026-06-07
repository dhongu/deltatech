## Security groups

Two groups are provided. Assign users before they can access the Agreement menu:

- **Agreement / User** (`group_agreement_user`) — can view and create agreements;
  also grants access to the Agreements smart button on partner records.
- **Agreement / Manager** (`group_agreement_manager`) — includes User rights plus
  access to the Configuration menu (agreement types management). The Administrator
  user is assigned to this group by default.

Go to **Settings → Users** and add the relevant group to each user.

## Agreement types

Before creating agreements, configure at least one agreement type under
**Agreement → Configuration → Agreement types**. Each type requires:

- **Type** — a label identifying the kind of agreement (e.g. "Service Contract",
  "NDA", "Supply Agreement").
- **Sequence** — an `ir.sequence` record that will supply the auto-generated
  reference number when **Get number** is clicked on an agreement form.
- **Layout** (optional) — an `ir.actions.report` record (a QWeb report) used when
  **Print** is clicked on an agreement form. If not set, printing will raise an error.
