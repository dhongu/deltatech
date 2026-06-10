## 18.0.1.0.2 (2026-06-10)

- Fix `TypeError` (500 Internal Server Error) on `/shop/address`: `_prepare_address_form_values()` now uses a tolerant `*args, **kwargs` signature, compatible with newer Odoo 18 builds that pass `use_delivery_as_billing` positionally.
