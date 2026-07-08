1. Go to **Settings > General Settings**, find the **Database Is Neutralized** toggle (next to the Companies settings).
2. Enable it to mark the database as a test/staging system:
   - A "test system" banner is enabled on all pages (the standard Odoo neutralization banner is activated).
   - The **Apps** list shows a "Database is Neutralized" indicator and unlocks the install/uninstall buttons on modules even when they are normally blocked outside neutralized databases.
   - Saving with the toggle turned on for the first time also runs the neutralization SQL scripts (`data/neutralize.sql`) shipped by any currently installed module, e.g. to scrub API keys, webhooks, or scheduled emails.
3. Leave it disabled (default) for production databases — the banner and messages will show "It is a productive system" instead.
