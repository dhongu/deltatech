Scoate mișcările de stoc închise din **fișa de magazie** a localizării românești (modulul
`l10n_ro_stock_report`): după închiderea unei perioade sau a unui an fiscal, fișa de magazie se poate
rula doar pe mișcările de stoc încă deschise.

- **Indicatorul Valuation Active**: Fiecare mișcare de stoc primește indicatorul **Valuation Active**,
  activ implicit; o mișcare cu indicatorul dezactivat e considerată închisă. În Odoo 19 evaluarea se
  ține pe mișcarea de stoc, deci indicatorul stă acolo.
- **Opțiunea Only active**: Asistentul fișei de magazie primește opțiunea **Only active**; când e
  bifată, soldul inițial, intrările, ieșirile și soldul final nu mai iau în calcul mișcările închise.
- **Raportul rămâne altfel neschimbat**: Cu opțiunea nebifată, fișa de magazie e exact cea din
  localizarea românească; mișcările de stoc nu sunt ascunse nicăieri altundeva în Odoo.

Indicatorul **Valuation Active** nu apare pe formularul mișcării de stoc în această versiune: se setează
prin import sau printr-un script.

**Date trimise în afara Odoo:** niciuna.
