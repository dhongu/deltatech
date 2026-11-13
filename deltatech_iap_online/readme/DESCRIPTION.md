The base of the Terrabit services for **Odoo Online**: data-only modules (no Python, imported as a
zip) send their requests to a Terrabit server, which does the heavy work and writes the answer back
in your database. This module holds what all those services share; each service module adds only
its own fields, buttons and the way it writes the answer.

- **One account per service**: *Settings > Technical > Terrabit Services* lists the services
  installed, with their credits left.
- **Activation in one click**: the **Activate** button registers the database at the Terrabit
  server; the account token comes back by itself, with the trial credits of the service. Nothing to
  copy or paste.
- **Buy and check credits**: **Buy Credits** opens the credit page of your account on the Terrabit
  server; **Refresh Credits** asks the credits left, which are also updated with every answer.
- **Requests you can follow**: *Terrabit Services > Requests* shows each request, its status and the
  error, if any. A request without answer after 10 minutes is sent once more.
- **Safe answers**: the answer comes on an *On webhook* automation whose secret URL accepts only a
  request still waiting, identified by its token.
- **What leaves your database**: the input of the request, its token, the address of your database
  (for the answer) and, at activation, the name and the Tax ID of the company.

For developers: a service module creates an `x_iap_online_service` record (`x_code`, `x_server`) and,
optionally, an *apply* server action (`x_apply_action_id`) that receives the answer in the context
key `iap_answer`; its documents create `x_iap_online_request` records with `x_kind = 'request'`.
