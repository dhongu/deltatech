Odoo a eliminat câmpul `qty_multiple` de pe `stock.warehouse.orderpoint` la trecerea
la versiunea 19.0 (commit `09d6c79f0e4`, "replace `qty_multiple` by replenishment
unit in orderpoints"), înlocuindu-l cu `replenishment_uom_id` - o unitate de măsură
alternativă legată explicit de produs sau de furnizor. Matematic mecanismul e
echivalent, dar necesită UoM-uri configurate per produs/furnizor - infrastructură
care de regulă nu există deja pentru clienții care doar aveau un multiplu simplu
(ex. "100 buc/cutie") completat pe regula de aprovizionare.

Acest modul reintroduce `qty_multiple` exact ca în Odoo <= 18.0, cu aceeași logică
de rotunjire, fără nicio dependență de unități de măsură suplimentare. Dacă
`qty_multiple` e setat pe o regulă de aprovizionare, cantitatea de comandat se
rotunjește direct la un multiplu al acestei valori; altfel comportamentul nativ
(`replenishment_uom_id`) rămâne neschimbat.
