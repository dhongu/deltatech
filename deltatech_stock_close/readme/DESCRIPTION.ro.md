Scoate înregistrările de evaluare a stocului închise din **fișa de magazie** a localizării românești
(modulul `l10n_ro_stock_report`): înregistrările de evaluare care nu mai contează se pot arhiva, iar
fișa de magazie se poate rula apoi doar pe cele active.

- **Înregistrări de evaluare arhivabile**: Înregistrările de evaluare a stocului primesc câmpul
  *Active*, deci se pot arhiva din *Inventar > Raportare > Evaluare*; înregistrările de evaluare ale
  unui transfer le arată și pe cele arhivate.
- **Opțiunea Only active**: Asistentul fișei de magazie primește opțiunea **Only active**; când e
  bifată, soldul inițial, intrările, ieșirile și soldul final nu mai iau în calcul înregistrările
  arhivate.
- **Mai mult pe liniile fișei**: Liniile de intrare și de ieșire ale fișei de magazie păstrează și tipul
  operațiunii și data facturii.

**Important:** o înregistrare de evaluare arhivată nu mai intră nici în evaluarea standard a stocului
din Odoo (valoarea și cantitatea evaluată a produselor, raportul de evaluare), nu doar în fișa de
magazie. Arhivați înregistrări doar după ce verificați efectul asupra evaluării produselor respective.

**Date trimise în afara Odoo:** niciuna.
