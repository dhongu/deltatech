Extends the standard Odoo Contacts module with additional personal data fields for individual contacts, including Romanian CNP (Personal Numeric Code) with checksum validation, identity card details, birthdate, gender, and means of transport.

**Key features:**

- Adds a **Personal Data** tab on the contact form (visible for individual contacts only) with fields: CNP, birthdate, gender, identity card series/number, issuing authority, and issue date.
- **CNP validation**: validates the 13-digit Romanian Personal Numeric Code checksum on save; silently clears invalid CNPs imported in bulk (`install_mode` context).
- **Auto-fill from CNP**: when a CNP is entered, birthdate and gender are automatically derived from the code digits.
- **Contact name display**: optionally suppresses the parent company name from contact display names, controlled by a system parameter (`contact.get_name_only`).
- **Means of transport** field on the contact record.
- **Enhanced search filters**: adds Delivery and Invoice address type filters to the Contacts search view.
- **Inline address display**: supports context flags `show_phone`, `show_category`, and `address_inline` to enrich or flatten the contact display name in relational fields.
