## Part of the Terrabit POS Ecosystem

- **deltatech_pos_stock** — the stock and price badge on the product card; this module adds the
  other shops to it and reuses its live-bus channel
- **deltatech_pos_price_sync** — pushes live price changes to open POS sessions
- **deltatech_pos** / **deltatech_pos_base** — fiscal receipts on Romanian cash registers

Standard Odoo 19 already lists the stock per warehouse in the product info popup, but only online,
one product at a time and with every warehouse of the company. This module puts the figure on
the card and in a filter, limits it to the shops, and keeps it available offline.
