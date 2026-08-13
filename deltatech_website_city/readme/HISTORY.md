## 18.0.1.2.1 (2026-08-13)

- Test: the carrier city filter at checkout is covered end to end -- filtered on the delivery address, whole on a billing address, whole again when no carrier is chosen, when the carrier has no catalog, or when its catalog covers nothing in that county, and a locality outside the catalog refused on submit.

## 18.0.1.2.0 (2026-08-13)

- Imp: on the checkout delivery address, the locality list is limited to the localities known by the selected carrier, when that carrier ships with its own locality catalog (`delivery.carrier._get_city_domain()`). Both the initial rendering and the `/shop/state_infos` lookup apply the filter, and a submitted locality outside the catalog is rejected server side. The filter is skipped when no carrier is selected yet, when the carrier has no catalog, or when its catalog holds no locality in that state, so the customer is never left with an empty list.

## 18.0.1.1.4 (2026-06-10)

- Fix `TypeError` (500 Internal Server Error) on `/shop/address`: `_prepare_address_form_values()` now uses a tolerant `*args, **kwargs` signature, compatible with newer Odoo 18 builds that pass `use_delivery_as_billing` positionally.
