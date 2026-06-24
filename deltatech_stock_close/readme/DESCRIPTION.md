Stock Closing Operations
========================

This module provides tools for managing stock closing operations at a specific date.
It helps maintain inventory accuracy by allowing users to mark stock move valuations as closed, so they can be excluded from the Romanian storage sheet after a certain period or when closing the fiscal year.

Key Features
------------

- Ability to close stock operations as of a given date.
- Adds a "Valuation Active" field on stock moves (Odoo 19 stores valuation on stock moves) for better visibility.
- Improves reporting performance by filtering out old or closed stock move valuations in the storage sheet ("Only active" option).
- Integration with Romanian localization stock reports.

Usage
-----

- Go to Inventory > Reporting > Romanian Stock Storage Sheet.
- Enable the "Only active" option to exclude closed valuations from the report.
- Mark stock move valuations as closed (unset "Valuation Active") according to your business needs.
