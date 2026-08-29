Key Features
============

This module provides an efficient way to manage transactions for generic or anonymous partners by allowing the definition of a specific "Generic Partner" in the Odoo configuration.

Features:
---------

- Define a default "Generic Partner" to be used when a specific partner is not required.
- Automatically handles the selection of this partner in various business flows such as sales and invoicing.
- Helps simplify data entry for businesses that handle many one-time or anonymous customers.
- Fully integrated with Odoo's standard accounting and sales settings.
- Optionally protect the generic partner against accidental changes: once the
  protection is enabled, users can no longer rename, archive or delete it.

Usage:
------

1. Navigate to Settings > General Settings > Sales.
2. Locate the "Generic Partner" configuration section.
3. Select an existing partner (e.g., "Generic Customer") or create a new one to serve as the default.
4. This partner will then be used as a fallback in the relevant modules.

Protecting the generic partner:
-------------------------------

The generic partner is reachable from every sales document, so it is easily
mistaken for a normal customer and edited by accident. Tick **Protect Generic
Partner** in the same settings section to prevent this: the contact form then
shows a warning banner and any change is refused when saving.

The protection is disabled by default, so existing databases keep their current
behaviour. Users who legitimately have to change the partner are given the
**Generic Partner: Editor** group; Settings administrators already have it.

Writes performed by Odoo itself — chatter, activities, portal signup tokens,
geolocation — stay allowed, as do automated flows running with elevated rights.
