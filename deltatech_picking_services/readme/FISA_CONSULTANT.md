# Fișă Modul: Servicii înregistrate pe transfer

**Modul:** `deltatech_picking_services`
**Utilizator principal:** Gestionar / operator depozit
**Prioritate:** 🟢 Scăzută (evidență informativă pe transfer, fără efect în stoc sau contabilitate)

---

## 1. Scop business

Pe lângă mărfurile mutate, un transfer de stoc are uneori servicii legate de el: transport, manipulare,
paletizare, ambalare. În Odoo standard, un transfer conține doar produse care se mișcă în stoc, deci
serviciile nu au unde fi notate. Modulul adaugă pe transfer pagina **Services**, în care operatorul
înregistrează serviciile aferente, cu cantitate, preț unitar și subtotal, iar totalul se vede direct pe
transfer.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale: liniile de servicii nu generează mișcări de stoc, note
contabile sau facturi. Este o evidență operațională pe documentul de transfer, utilă pentru a ști ce
servicii s-au prestat la o recepție sau livrare și pentru a le factura sau deconta ulterior, prin
fluxurile standard de vânzare sau achiziție.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Gestionar / operator depozit | Adaugă, modifică și șterge serviciile de pe transfer |
| Consultant | Definește produsele de tip serviciu folosite pe transferuri |

Roluri recomandate pentru testare: **Inventory / User** (dreptul complet pe liniile de servicii). Fiecare
linie preia compania transferului și este vizibilă doar utilizatorilor cu acces la acea companie.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile.

Date minime pentru demo:

- unul sau două produse de tip **Service** (de exemplu *Transport*, *Manipulare marfă*);
- un transfer (recepție sau livrare) în orice stare.

## 5. Configurare inițială

1. Instalați modulul `deltatech_picking_services` (depinde doar de `stock`).
2. Creați produsele de tip serviciu: **Inventory → Products → Products → New**, **Product Type** =
   *Service*. Doar produsele de tip serviciu pot fi alese pe liniile paginii **Services**.

## 6. Flux de utilizare

### Pasul 1 — Adăugarea serviciilor pe transfer

Deschideți un transfer (**Inventory → Operations → Transfers → Receipts** sau **Deliveries**, apoi
transferul) și mergeți pe pagina **Services**, aflată după pagina operațiilor. Apăsați **Add a Service**
și completați rândul:

- **Service** — produsul de tip serviciu;
- **Description** — se completează cu numele serviciului; coloana este ascunsă implicit și se afișează din
  selectorul de coloane;
- **Quantity** — implicit 1;
- **Unit of Measure** — unitatea serviciului (vizibilă când sunt activate unitățile de măsură);
- **Unit Price** — prețul unitar.

**Subtotal** se calculează ca preț unitar × cantitate. Ordinea rândurilor se schimbă prin tragere.

### Pasul 2 — Verificarea totalului

Pe pagina **Services**, sub coloana **Subtotal**, se afișează totalul serviciilor transferului. Verificați
că fiecare rând are cantitatea și prețul corecte și că totalul corespunde valorii convenite cu
prestatorul sau clientul.

### Pasul 3 — Duplicarea și ștergerea transferului

La duplicarea transferului, liniile de servicii se copiază odată cu el. La ștergerea transferului,
liniile lui de servicii se șterg și ele.

### Note de monografie și raportare

Nu se generează note contabile (Dr/Cr). Facturarea serviciilor sau înregistrarea lor ca cheltuială se
face separat, prin factura de vânzare sau de furnizor.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `stock` | transferul pe care se adaugă pagina **Services** |
| `product` | produsele de tip serviciu |

**Ce e automat:** descrierea și unitatea de măsură propuse din serviciu, subtotalul și totalul,
copierea liniilor la duplicarea transferului, ștergerea lor odată cu transferul, filtrarea pe companie.

**Ce rămâne manual:** introducerea serviciilor și a prețurilor, facturarea sau decontarea lor.

## 8. Verificări pentru consultant

- [ ] Pagina **Services** apare pe formularul transferului, după pagina operațiilor.
- [ ] În coloana **Service** se pot alege doar produse de tip serviciu.
- [ ] La alegerea serviciului, **Description** și **Unit of Measure** se completează din produs.
- [ ] **Subtotal** = **Unit Price** × **Quantity**, iar totalul coloanei este suma subtotalurilor.
- [ ] Duplicarea transferului copiază liniile de servicii.
- [ ] Un utilizator fără acces la compania transferului nu vede liniile lui de servicii.
- [ ] Validarea transferului nu creează mișcări de stoc pentru servicii.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Câmp obligatoriu necompletat la salvare | Rând fără **Service** sau fără unitate de măsură | Alegeți serviciul; unitatea se completează din produs |
| Serviciul dorit nu apare în listă | Produsul nu este de tip *Service* | Schimbați tipul produsului sau folosiți alt serviciu |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița, bannerul, sigla și imaginea principală pentru Odoo Apps) și nici test
`tests/test_screenshots.py`. Dacă se doresc capturi, ele se generează cu skill-ul `fisa-screenshots`
(pagina **Services** cu câteva rânduri și totalul) și se leagă apoi în pașii din secțiunea 6.

## 11. Observații pentru manual

- Manualul trebuie să precizeze că liniile de servicii sunt doar evidență: nu se facturează și nu intră
  în stoc automat.
- Coloana **Description** este ascunsă implicit; utilizatorii care vor să o vadă o activează din
  selectorul de coloane al listei.
