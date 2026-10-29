## Scheduled action

1. Activate the developer mode and go to **Settings > Technical > Automation >
   Scheduled Actions**.
2. Create an action on the model **Followup Send Wizard** (`followup.send.wizard`),
   with the frequency you want (usually daily), and this Python code:
   - for all the followups: `model.run_followup()`
   - for selected followups only: `model.run_followup(["f-1", "AZI"])`, where the
     values are the **Code** of the followups to run.
3. The user of the scheduled action needs the **Followup manager** group.

## Mail template

Create a mail template on the model **Contact**. In its body you can use
`${object.name}`, `$total_debit`, `$total_all_debit`, `$total_due_debit`,
`$currency` and `[invoices]`. By default the template deletes the mail after it
is sent (**Auto Delete**); untick it if you want to keep a trace in
**Settings > Technical > Email > Emails**.

## Testing

To test without writing to customers, create the system parameter
`followup.override_partner_id` (**Settings > Technical > Parameters > System
Parameters**) with the id of a contact: the e-mails go to that contact instead of
the customers. Remove the parameter before going live.
