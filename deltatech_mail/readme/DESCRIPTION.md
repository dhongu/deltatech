Test and training databases must not send real emails to customers. This module redirects outgoing emails to another address, sets the sender, and rewrites text in posted messages.

- **Redirect recipients**: A *Receiver* rule under *Substitution* sends the emails of its *Related Document Model* to its *Substitution* address instead of the real recipients, and drops the CC copies. With no model, it redirects every email.
- **Fixed sender**: A *Sender* rule sets its address as the sender of the matching outgoing emails; the first matching rule applies.
- **Company sender**: When the system parameter `mail.use_company_email` is `True`, posted messages and queued emails go out from the company email address. Posting a message is refused if the company has no email.
- **Body text replacement**: Under *Body Substitution*, the *Body Part* text is replaced by the *Substitution* text in every message posted on a record. Messages already posted stay as they are, and the match includes formatting.

The module depends on Discuss (`mail`). The rules apply to all users and companies; only Settings administrators can change them, and other internal users can only read them. A *Receiver* rule with no model redirects every outgoing email, so remove it before going live.
