## 19.0.1.2.1 (2026-08-13)

- Fix: the locality filter read the cart through `website.sale_get_order()`, which no longer exists in 19.0, so `/portal/state_infos` raised as soon as a session had a cart. The cart is now read from `request.cart`.
- Test: the carrier city filter at checkout is covered end to end -- filtered on the delivery address, whole on a billing address, whole again when no carrier is chosen, when the carrier has no catalog, or when its catalog covers nothing in that county, and a locality outside the catalog refused on submit.

## 19.0.1.2.0 (2026-08-13)

- Imp: on the checkout delivery address, the locality list is limited to the localities known by the selected carrier, when that carrier ships with its own locality catalog (`delivery.carrier._get_city_domain()`). Both the rendering and the `/portal/state_infos` lookup apply the filter, and a locality submitted outside the catalog is rejected server side. Only the delivery address is concerned. The filter is skipped when no carrier is selected yet, when the carrier has no catalog, or when its catalog holds no locality in that state, so the customer is never left with an empty list.
