**Deltatech Credentials** provides a centralised store for external service credentials
within Odoo. Instead of scattering API keys, tokens, and login pairs across system
parameters or configuration files, administrators can manage all access data in one
secure location — available directly under **Settings > Users & Companies > Credentials**.

**Key features:**

- Store credentials for any external service with a descriptive name and optional code.
- Three access-type modes: **User / Password**, **Client ID / Client Secret (API key)**,
  and **Access Token** — only the relevant fields are shown for each mode.
- Password field is masked in the UI for security.
- Access restricted to Odoo Administrators (`base.group_system`) out of the box.
- Designed as a shared dependency: other Deltatech modules (integrations, EDI connectors,
  API bridges) can reference `access.credentials` records to retrieve their credentials
  programmatically, keeping secrets out of module settings.
