- **Send outgoing mail as the company address**: go to **Settings >
  Technical** (or via the `mail.use_company_email` system parameter) and
  enable **Use Company Email**. When enabled, all outgoing messages use
  the current user's company name/email as the `From` address instead
  of the user's own email; the company must have an email configured or
  sending will raise an error.
- **Redirect/substitute recipients**: go to **Settings > Technical >
  Email > Substitution** and create entries with a target document
  model (or leave it empty to apply to all models), an email address,
  and a type (**Sender** or **Receiver**). Matching outgoing emails are
  redirected to (or their sender replaced with) the configured address
  — useful for testing/staging environments where you don't want real
  emails to reach customers.
- **Substitute text/HTML in message bodies**: go to **Settings >
  Technical > Email > Body Substitution** and create entries pairing a
  **Body Part** (HTML snippet to search for) with a **Substitution**
  (HTML to replace it with). Every message posted afterwards (via
  `message_post`) has these replacements applied automatically.
