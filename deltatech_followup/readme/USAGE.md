1. Go to **Accounting > Configuration > Followups** (menu under Account Management) to define followup items. For each one, set:
   - **Name** and **Code** (the code can be used to target specific followups from a cron job).
   - **Active** — whether the followup is currently processed.
   - **Date field to use** — Invoice date or Due date.
   - **Days from** — relative days from the chosen date (negative to send before, positive to send after).
   - **Comparator** — Equal (only the exact matching date) or Greater or equal.
   - **Only open invoices**, **Parse refund invoices**, **Use customer currency**, **Amount margin** as needed.
   - **Mail template** (must be a `res.partner` model template) and, optionally, an **Invoices placeholder** HTML block that supports placeholders such as `$number`, `$date_due`, `$amount_total`, `$amount_due`, `$total_debit`, `$currency`, etc.
2. On each customer's contact form, tick **Send followup e-mails** to include that partner in followup processing (field `send_followup` on `res.partner`).
3. Followups are normally sent through a scheduled action: configure a cron job on model **Followup Send** (`followup.send.wizard`) with Python code `model.run_followup()` to run all active followups, or `model.run_followup(["12D", "20D"])` to run only the followups with those codes.
4. To trigger a followup immediately for testing, open the followup record and use the **Send now** server action.
5. To test without emailing real customers, set the system parameter `followup.override_partner_id` to the id of a test partner — all followup e-mails will be redirected to that partner.
