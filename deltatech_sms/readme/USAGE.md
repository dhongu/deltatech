This module lets Odoo send SMS through a custom gateway instead of Odoo's IAP SMS service. It only needs to be configured once, then SMS sent from anywhere in Odoo (sale confirmations, marketing, etc.) will go through the selected provider.

1. Go to **Settings > Technical > IAP > Account** (developer mode required), open the SMS account, and set:
   - **SMS Provider**: `SMS 4Pay` or `SMS Wapi`.
   - **SMS Secret**: the API password/secret for that provider.
   - **SMS Gateway**: the provider's service ID (4Pay) or device ID (Wapi).
2. From then on, every SMS Odoo sends is routed through the configured provider's HTTP API instead of the default Odoo IAP SMS credits.
