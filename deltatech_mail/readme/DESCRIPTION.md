Test and training databases must not send real emails to customers. This module redirects outgoing emails to another address, can send them from the company address, and rewrites text in posted messages.

- **Redirect recipients**: A *Receiver* rule under *Substitution* sends the emails of its *Related Document Model* to its *Substitution* address instead of the real recipients. With no model, it redirects every email.
- **Company sender**: When the system parameter `mail.use_company_email` is `True`, queued emails go out from the email address of the author's company. An email is not sent if that company has no email address.
- **Body text replacement**: Under *Body Substitution*, the *Body Part* text is replaced by the *Substitution* text in every message posted on a record. Messages already posted stay as they are, and the match includes formatting.

The module depends on Discuss (`mail`). The rules apply to all companies. Internal users can read, create, and edit them, and only Settings administrators can delete them. A *Receiver* rule with no model redirects every outgoing email, so remove it before going live.
