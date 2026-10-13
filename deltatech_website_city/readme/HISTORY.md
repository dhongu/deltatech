## 19.0.1.2.5 (2026-10-09)

- Fix: the upgrade from 18.0 left the old view `address` (inheriting `website_sale.address` on `div_city`) in the database, and every website reported it as a broken template. A migration removes it; the city field is added by the view `address_form_fields`.

## 19.0.1.2.4 (2026-10-01)

- Test: the free-text city test posts its phone number in international format. With `deltatech_website_phone_validation` installed, a national number could not be parsed for the fictitious test country and the address was refused for the phone, failing the `website` CI shard.

## 19.0.1.2.3 (2026-10-01)

- Fix: an address saved at checkout kept only the chosen locality (`city_id`) and left the free-text `city` empty, a step lost in the 19.0 migration. Posting the invoice of such a customer was refused for a missing city. The city is filled again from the chosen locality, and a migration fills it on the partners already saved without it.

## 19.0.1.2.2 (2026-09-30)

- New module icon in the flat style of the other modules; it replaces the old one.

## 19.0.1.2.1 (2026-08-13)

- Fix: the locality filter read the cart through `website.sale_get_order()`, which no longer exists in 19.0, so `/portal/state_infos` raised as soon as a session had a cart. The cart is now read from `request.cart`.
- Test: the carrier city filter at checkout is covered end to end -- filtered on the delivery address, whole on a billing address, whole again when no carrier is chosen, when the carrier has no catalog, or when its catalog covers nothing in that county, and a locality outside the catalog refused on submit.

## 19.0.1.2.0 (2026-08-13)

- Imp: on the checkout delivery address, the locality list is limited to the localities known by the selected carrier, when that carrier ships with its own locality catalog (`delivery.carrier._get_city_domain()`). Both the rendering and the `/portal/state_infos` lookup apply the filter, and a locality submitted outside the catalog is rejected server side. Only the delivery address is concerned. The filter is skipped when no carrier is selected yet, when the carrier has no catalog, or when its catalog holds no locality in that state, so the customer is never left with an empty list.
