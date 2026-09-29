## 20.0.1.2.2 (2026-09-30)

- New module icon in the flat style of the other modules; it replaces the old one.

## 20.0.1.2.1 (2026-09-27)

- Mig: in 20.0 the city dropdown of the address form is standard in `portal` (`div_city_id`, `cities_data`, `/my/address/state_info`, ZIP filled from the chosen city), but only for BR, CL, PE, CO and TW. The module is now an extension of it: `res.country._enforce_city_choice()` enables it for every country with *Enforce Cities* and at least one city; the own city select, the field reordering and the `/portal/state_infos` lookup of the form are dropped in favour of the standard ones (the route is kept for compatibility).
- Mig: the mandatory address fields are computed on `res.partner._get_mandatory_address_fields()` (moved from the portal controller in 20.0); the state stays required when the city is chosen from the list, and the localities are loaded with the state instead of rendering the whole catalog of the country.
- Mig: the carrier locality catalog applies to the standard `/my/address/state_info` route and to the rendered `cities_data`; the address form sends the address type along with the state.

## 19.0.1.2.1 (2026-08-13)

- Fix: the locality filter read the cart through `website.sale_get_order()`, which no longer exists in 19.0, so `/portal/state_infos` raised as soon as a session had a cart. The cart is now read from `request.cart`.
- Test: the carrier city filter at checkout is covered end to end -- filtered on the delivery address, whole on a billing address, whole again when no carrier is chosen, when the carrier has no catalog, or when its catalog covers nothing in that county, and a locality outside the catalog refused on submit.

## 19.0.1.2.0 (2026-08-13)

- Imp: on the checkout delivery address, the locality list is limited to the localities known by the selected carrier, when that carrier ships with its own locality catalog (`delivery.carrier._get_city_domain()`). Both the rendering and the `/portal/state_infos` lookup apply the filter, and a locality submitted outside the catalog is rejected server side. Only the delivery address is concerned. The filter is skipped when no carrier is selected yet, when the carrier has no catalog, or when its catalog holds no locality in that state, so the customer is never left with an empty list.
