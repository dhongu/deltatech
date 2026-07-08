This module works automatically, with no configuration needed.

- A scheduled action (cron) periodically recomputes, for each product, the
  **Minimum purchase price**, **Maximum purchase price** and **Average
  purchase price** from vendor bill lines posted in the last 12 months.
- The three fields are shown on the product template form, in the Purchase
  tab.
- Values are always expressed in the company's currency; in multi-company
  environments with different currencies per company this is not reliable,
  so the module is not recommended in that setup.
