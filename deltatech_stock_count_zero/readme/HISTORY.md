## 20.0.0.0.4 (2026-10-14)

- Translations: .pot regenerated on 20.0 and Romanian translation completed for the new terms.

## 20.0.0.0.3 (2026-10-14)

- Fix: when a selected quant is outdated (moved since the count), the conflict wizard of the inventory adjustment is opened; before, the result was ignored and the count was not applied, without any message.
- Fix: "Set Count to Zero" is restricted to the inventory administrators (`stock.group_stock_manager`), like the standard "Set to 0"; the wizard refuses the option for the other users.
- Fix: for products tracked by lot/serial number only the selected quants are set to zero and applied; the other lots of the product in the same location are no longer zeroed.

## 19.0.0.0.2 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
