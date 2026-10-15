# Funcționalitățile modulului de la 16.0 la 20.0

Notă internă (15.10.2026), pe baza codului de pe `origin/16.0` … `origin/20.0`. Arată ce
făcea modulul în fiecare versiune, ce s-a pierdut la migrări și ce a preluat Odoo
standard, ca să nu se piardă din nou la migrările următoare.

## Ce s-a schimbat la fiecare versiune

- **16.0 (16.0.2.1.4)** — varianta cea mai completă:
  - controllerul `/shop/carrier_acquirer_check` și override pe `cart_carrier_rate_shipment`;
  - `website.sale_get_order` punea `force_provider_id` în context (taxa de ramburs din
    `deltatech_delivery` intra în prețul livrării);
  - scriptul `website_sale_delivery.js` pe `/shop/payment` (livrarea și plata erau pe
    aceeași pagină): ascundea plățile nepermise de metoda de livrare, bloca butonul de
    plată pentru o combinație invalidă și recalcula livrarea la alegerea plății;
  - șabloane QWeb: logoul metodei de livrare, ascunderea plăților și a livrărilor după
    etichetele utilizatorului, plata preselectată din `res.partner.provider_id`;
  - `sale.order.provider_id`, scris la confirmare din ultima tranzacție;
  - greutate min/max pe livrare (`_get_delivery_methods`).
- **17.0** — controllerul, `website.py`, `sale.order.provider_id` și `submit_txt` scoase
  (`9b5fc5164`, `fbe68dcb1`, `5d3779ff9`). Limita de valoare și etichetele plății trec pe
  server (`_get_compatible_providers`); filtrarea după livrare rămâne doar în browser
  (`payment_form.esm.js`, atributul `data-acquirer-allowed-ids`). Comentate: restricția
  livrării după etichetă și preselecția plății din `provider_id`. `force_provider_id` nu
  mai e setat de nimeni, deci taxa de ramburs nu se mai vede la checkout. Bloc nou pe
  pagina de confirmare (`5ba907487`).
- **18.0** — Odoo mută livrarea pe `/shop/checkout`, plata rămâne pe `/shop/payment`.
  Logoul și blocul de confirmare dispar. `ac62ac6e8` (03.2026) adaugă filtrarea după
  livrare pe server; scriptul rescris pe `WebsiteSaleCheckout` nu are efect (pe pagina de
  checkout nu există plăți).
- **19.0** — `8ddf65b19` (12.2025): intersecția cu livrarea în `_get_compatible_providers`
  și restricția livrării după eticheta partenerului pe server (pe
  `commercial_partner_id`), cu teste. Scriptul și logoul sunt comentate.
- **20.0** — filtrarea în `_find_available_providers` (`_get_compatible_providers` nu mai
  există), cu motivul fiecărei excluderi în raportul de disponibilitate; scriptul
  comentat și override-ul mort `_check_carrier_quotation` au fost șterse; câmpurile de
  greutate apar pentru toate tipurile de livrare.
- **20.0.2.2.0** — recuperate punctele 1–4 din propuneri: garda la crearea tranzacției
  (`_validate_transaction_for_order`, aceeași logică ca filtrul, în
  `payment.provider._filter_allowed_for_order`) și livrările fără furnizor express scoase
  din checkout-ul express; etichetele plății citite pe `commercial_partner_id`;
  plata preselectată din `res.partner.provider_id`; logoul livrării pe `/shop/checkout`;
  `data-acquirer-allowed-ids` și blocurile comentate scoase.

## Funcționalitate × versiune

Legendă: ✅ funcționează · ⚠️ parțial · ❌ pierdută · 🔄 acoperită de Odoo standard ·
➖ nu există în versiunea respectivă

| Funcționalitate | 16 | 17 | 18 | 19 | 20 |
|---|---|---|---|---|---|
| Plăți permise după metoda de livrare, pe server | ⚠️ | ❌ | ✅ | ✅ | ✅ |
| Aceeași filtrare live, în browser | ✅ | ✅ | ❌ | ❌ | ❌ (nu mai e necesară) |
| Limita de valoare a plății (`value_limit`) | ✅ | ✅ | ✅ | ✅ | ✅ (dublează `maximum_amount`) |
| Plăți restricționate după eticheta partenerului | ✅ | ✅ | ✅ | ✅ | ✅ (pe partenerul comercial, recuperat în 20.0.2.2.0) |
| Livrări restricționate după eticheta partenerului | ✅ | ❌ | ❌ | ✅ | ✅ |
| Greutate min/max pe livrare | ✅ | ✅ | ✅ | ✅ | ✅ (max-ul dublează `max_weight`) |
| Plata preselectată din `res.partner.provider_id` | ✅ | ❌ | ❌ | ❌ | ✅ recuperat în 20.0.2.2.0 |
| Logoul metodei de livrare în magazin | ✅ | ✅ | ❌ | ❌ | ✅ recuperat în 20.0.2.2.0 |
| Furnizorul reverificat la crearea tranzacției (inclusiv checkout express) | ⚠️ | ❌ | ❌ | ❌ | ✅ recuperat în 20.0.2.2.0 |
| Taxa de ramburs recalculată la alegerea plății | ✅ | ❌ | ❌ | ❌ | ❌ |
| `sale.order.provider_id` la confirmare | ✅ | ❌ | ➖ | ➖ | 🔄 `transaction_ids` |

## De ce nu mai e nevoie de filtrarea în browser

Pe 20 livrarea se alege pe `/shop/checkout`, iar plata pe `/shop/payment`, generată la
fiecare vizită cu filtrul de pe server (`_get_shop_payment_values` trimite
`sale_order_id`). Pe `/shop/payment` livrarea nu se mai poate schimba.

Rămâneau două goluri, ambele pe server (acoperite în 20.0.2.2.0 de garda la crearea
tranzacției):

- **Checkout-ul express** (Google/Apple Pay din coș): furnizorul se alege înainte de
  livrare, iar clientul poate alege apoi orice livrare din portofel.
- **Crearea tranzacției nu reverifică furnizorul** față de livrarea aleasă.

## Ce acoperă Odoo 20 standard

- `payment.provider.minimum_amount` / `maximum_amount`, cu conversie în moneda
  companiei (`value_limit` compară `amount_total` în moneda comenzii);
- restricții pe furnizor după țară și monedă (`available_country_ids`,
  `available_currency_ids`);
- `delivery.carrier.allow_cash_on_delivery` (ramburs doar pe livrările bifate);
- `website_sale_collect` (plata la ridicare doar pentru ridicarea din magazin);
- `max_weight` / `max_volume`, țară / județ / cod poștal pe livrare;
- `must_have_tag_ids` / `excluded_tag_ids` pe livrare (pe etichete de produs, nu de
  partener).

Standardul nu are: listă de plăți permise pe livrare, greutate minimă, restricții după
eticheta partenerului, logo pe livrare.

## De recuperat pe 20 (propuneri)

Punctele 1–4 sunt implementate în 20.0.2.2.0; 5 și 6 rămân deschise.

1. **Gardă la crearea tranzacției** — override pe
   `PaymentPortal._validate_transaction_for_order(tx, order)`
   (`website_sale/controllers/payment.py`, hook gol în standard): `ValidationError` dacă
   `order.carrier_id.acquirer_allowed_ids` nu conține `tx.provider_id` (plus limita de
   valoare și etichetele). Opțional, în `_get_delivery_methods_express_checkout` se scot
   livrările care nu permit niciun furnizor cu checkout express. ~0,5–1 zi.
2. **Curățenie** — atributul `data-acquirer-allowed-ids` și blocurile comentate din
   `templates.xml`; etichetele: plata se uită la `order.partner_id`, livrarea la
   `commercial_partner_id` — de unificat pe `commercial_partner_id`.
3. **Plata preselectată din `res.partner.provider_id`** — pe 20 opțiunile sunt
   `payment.method`: în `_get_shop_payment_values` se adaugă metoda preferată (prima al
   cărei furnizor e cel al partenerului comercial), iar `payment.form` primește valoarea
   pentru `selected_method_id`. ~0,5 zi. Alternativ câmpul se scoate, dacă bazele
   clienților nu au valori completate.
4. **Logoul pe livrare** — moștenire pe `website_sale.delivery_method`. ~1 oră.
5. **`value_limit` → `maximum_amount`** — script de migrare (atenție la diferența de
   monedă). ~0,5 zi.
6. **Taxa de ramburs live** — ține de `deltatech_delivery`
   (`bitshop_delivery/deltatech_delivery/models/delivery.py` citește încă
   `force_provider_id`, pe care nu-l mai setează nimeni din 17.0). ~1–2 zile.

## Proiecte

flodel, datus și ridacon au modulul în manifestul `terrabit_<client>`, împreună cu
`deltatech_payment_on_delivery`; niciun modul propriu nu moștenește din el. Singura
dependență de cod e `force_provider_id` din `deltatech_delivery`. Înainte de punctele 3
și 5, de verificat în bazele lor dacă `delivery.carrier.acquirer_allowed_ids`,
`payment.provider.value_limit` / `restrict_label_ids` și `res.partner.provider_id` au
valori.
