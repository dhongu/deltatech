Permite afișarea unui logo diferit în rapoartele PDF (factură, ofertă/comandă,
aviz de livrare) în funcție de **echipa de vânzare** a documentului.

Util pentru companiile care operează mai multe branduri sub aceeași firmă
juridică: fiecare echipă de vânzare poate avea propriul logo, iar acesta este
folosit automat în antetul rapoartelor.

## Funcționare

- Se adaugă un câmp **Logo** pe echipa de vânzare (`crm.team`).
- La randarea raportului, dacă documentul are o echipă de vânzare cu logo
  propriu, se folosește acel logo; altfel se folosește logo-ul firmei.
- Mecanismul este generic, în dispecerul `web.external_layout`, deci acoperă
  toate variantele de layout (standard, striped, boxed, bold, folder, wave,
  bubble) și orice document care are câmpul `team_id`:
  - `sale.order` (ofertă/comandă) — `team_id` nativ
  - `account.move` (factură) — `team_id` nativ
  - `stock.picking` (aviz/livrare) — `team_id` calculat din comanda sursă

Dacă echipa nu are logo configurat, comportamentul rămâne identic cu cel
standard (logo-ul firmei).
