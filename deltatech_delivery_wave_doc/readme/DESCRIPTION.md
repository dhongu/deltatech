

Titlu: Vendor Delivery Document → Wave (Batch Picking)

Scop
- Modulul permite înregistrarea unei „note de livrare” de la furnizor (document cu linii: produs, cantitate, preț) și generarea automată a unui Batch/Wave care reunește recepțiile (pickings) deschise provenite din comenzi de achiziție (PO) existente pentru acel furnizor.

Problemă adresată
- Furnizorul livrează în timp, parțial și amestecat, pe baza unui document propriu (număr/serie).
- În standard, recepțiile trebuie procesate per PO; acest modul accelerează operațional recepțiile grupându-le într-un singur Wave pe baza documentului de livrare.

Caracteristici cheie
- Obiect nou: „Vendor Delivery Document” cu câmpuri: Furnizor, Dată, Număr document, Linii (Produs, Cantitate, UoM, Preț – informativ), Responsabil, Tip de operație (opțional), „Allow excess”.
- Buton „Generate Wave” pe document:
  - caută recepțiile de tip „incoming” pentru același furnizor și produsele din document, în stări confirmed/assigned;
  - alocă cantitățile din document peste cantitățile „deschise” din mișcările existente, în ordine cronologică (data programată a recepțiilor);
  - creează automat unul sau mai multe Wave-uri (un wave per combinație Operation Type × Companie) și atașează liniile de mișcare folosind API-ul standard `stock.move.line._add_to_wave`;
  - dacă documentul depășește cantitățile deschise din recepții:
    - blochează cu eroare (implicit), sau
    - doar loghează diferențele în chatter dacă este bifat „Allow excess”.
- Trasabilitate: mesaj în chatter cu lista wave-urilor create și, dacă e cazul, cu cantitățile neacoperite.
- Fără efecte în Purchase: nu se creează PO-uri sau recepții noi – se folosește exclusiv ceea ce există deja din PO-urile confirmate.

Navigare și UI
- Inventory → Vendor Deliveries → Delivery Documents.
- Formularele includ tab „Lines” pentru produse și tab „Waves” (read-only) cu valurile create.

Instalare (Odoo 17)
- Dependențe: `mail`, `stock`, `stock_picking_batch`, `purchase_stock`.
- După instalare, utilizatorii din grupul „Inventory / User” pot crea și procesa documente.

Utilizare – pași rapizi
1) Creați un „Delivery Document” și completați: Furnizor, Dată, Număr document; opțional: Operation Type (Receipts), Responsabil, Allow excess.
2) Adăugați linii cu produse și cantități (UoM). Prețul este informativ și nu influențează recepția.
3) Apăsați „Generate Wave”. Modulul:
   - identifică recepțiile deschise (din PO-uri existente) pentru furnizor și produsele din document;
   - alocă cantitățile și creează Wave-ul/Wave-urile necesare;
   - atașează recepțiile la Wave pentru procesare rapidă.
4) Continuați procesarea valului/valurilor din Inventory (recepție, validare, etc.).

Note și limitări
- Toate transferurile dintr-un Wave trebuie să aparțină aceleiași companii și aceluiași Operation Type (regulă standard Odoo). Modulul va crea mai multe Wave-uri dacă este necesar.
- Dacă „Allow excess” nu este bifat, orice cantitate neacoperită de recepțiile deschise va bloca generarea Wave-ului cu un mesaj explicit pe produs.
- Modulul nu setează automat `qty_done`; atașează mișcările în Wave pentru execuție. (Se poate extinde ulterior pentru precompletare.)
- Prețurile din document sunt doar pentru referință; evaluarea stocului urmează regulile standard (pe baza PO/valuării configurate).

Compatibilitate
- Odoo 17.0 (Enterprise/Community) cu modulele listate la Dependențe.

Rulare rapidă pentru test (fără HTTP)
```
./odoo/odoo-bin -c odoo17.conf -d devtest_wave_doc \
  --stop-after-init --no-http \
  -i stock_picking_batch,deltatech_delivery_wave_doc \
  --log-level=info
```

