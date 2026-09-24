## 19.0.1.0.3 (2026-09-24)

- Port pe Odoo 19: `_default_inbound_payment_methods` și
  `_get_payment_method_information` rămân neschimbate în core-ul `account`
  pe O19, deci codul e portat verbatim (fără nicio adaptare de API).
  Necesar pentru migrarea clientului Ridacon (18.0→19.0): metoda de plată
  „Card Payment" e în uz productiv activ acolo.
