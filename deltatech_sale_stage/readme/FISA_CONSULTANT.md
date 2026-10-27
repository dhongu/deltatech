# Fișă Modul: Fazele comenzii de vânzare

**Modul:** `deltatech_sale_stage`
**Utilizator principal:** Operator back-office vânzări, responsabil logistică, manager vânzări
**Prioritate:** 🟡 Medie (util acolo unde comenzile trec prin pregătire, expediere și livrare prin curier și back-office-ul trebuie să știe în orice moment unde e fiecare comandă)

---

## 1. Scop business

Starea standard a comenzii de vânzare (Ofertă, Ofertă trimisă, Comandă de vânzare, Anulată) nu spune
nimic despre ce se întâmplă **după** confirmare: comanda e pregătită? a plecat la curier? a ajuns la
client? a fost refuzată? Modulul adaugă pe comandă un câmp **Phase** — o fază internă, definită de
companie, cu nume, culoare și ordine proprii — care avansează automat odată cu documentele comenzii:
trimiterea ofertei, confirmarea, validarea livrării, statusul curierului, facturarea, anularea.

Rezultatul: back-office-ul vede în listă, ca etichetă colorată, unde se află fiecare comandă și poate
filtra sau grupa comenzile pe fază, fără să deschidă livrările și facturile.

## 2. Bază legală și context

Modul operațional, fără temei legal sau fiscal. Fazele sunt etichete interne: **nu** schimbă starea
contabilă a comenzii, nu generează documente și nu postează note contabile. Contextul este de
organizare a fluxului de onorare a comenzilor (fulfilment) și de raportare internă a încărcării pe
etape.

## 3. Utilizatori și roluri

| Rol | Ce face | Grup Odoo |
|---|---|---|
| Manager vânzări | Definește fazele (nume, ordine, culoare, ce eveniment le activează, acțiune automată) | **Vânzări: Administrator** (`sales_team.group_sale_manager`) — drept complet pe faze |
| Operator vânzări / back-office | Vede faza pe comandă, o schimbă manual când e nevoie, filtrează și grupează | **Vânzări: Utilizator** — fazele sunt doar citire |
| Responsabil logistică | Validează livrările; statusul curierului mută comanda în faza corespunzătoare | Inventar: Utilizator |
| Contabil | Validează factura; comanda complet facturată trece singură în faza de facturare | Facturare **și** cel puțin **Vânzări: Utilizator** (citește fazele la validare) |

Roluri recomandate la testare: un **Administrator vânzări** pentru configurare, un **Utilizator
vânzări** pentru flux și un contabil cu **Facturare** și **Vânzări: Utilizator** pentru validarea
facturii.

## 4. Conturi și date implicate

Modulul nu atinge contabilitatea; nu există conturi implicate. Date folosite:

- **Fazele comenzii** (meniul **Vânzări → Configurare → Sale Order phase**): nume, secvență, cod,
  culoare și bifele de eveniment **Send Email**, **Confirmed**, **Pre Advice**, **Shipped**,
  **Delivered**, **Refused**, **Invoiced**, **Paid**, **Canceled**, plus o **Action** (acțiune server)
  opțională;
- **Tipul de operație** de stoc (ex. Livrări), pe care se poate seta o fază implicită;
- **Statusul de livrare** al transferului (`delivery_state`), completat de modulele de curierat
  (`deltatech_delivery_status` și conectorii de curier).

Date minime pentru demo: 5 faze în ordine (Ofertă trimisă → Confirmată → Pregătită → Expediată →
Facturată), un produs stocabil cu stoc, un client și tipul de operație **Livrări** al depozitului.

## 5. Configurare inițială

1. Mergeți la **Vânzări → Configurare → Sale Order phase** și creați fazele, în ordinea fluxului real
   (ordinea se schimbă prin tragere de mâner în listă; contează la avansarea automată):
   - „Ofertă trimisă” — bifă **Send Email**;
   - „Confirmată” — bifă **Confirmed**;
   - „Pregătită” — fără bifă de eveniment (se setează din tipul de operație, vezi pasul 2);
   - „Expediată” — bifă **Shipped**; „Livrată” — bifă **Delivered**; „Refuzată” — bifă **Refused**;
   - „Facturată” — bifă **Invoiced**; „Anulată” — bifă **Canceled**.
   Alegeți câte o **Color** pentru fiecare, ca eticheta să se distingă în listă.
2. Opțional, la **Inventar → Configurare → Tipuri de operații**, deschideți tipul **Livrări** și
   completați câmpul **Phase** (afișat sub **Depozit**) cu faza în care trebuie să treacă comanda la
   validarea livrării (ex. „Pregătită” sau „Expediată”).
3. Opțional, pe o fază, completați **Action** cu o acțiune server (ex. trimitere e-mail, notificare
   internă, apel de integrare) — ea rulează de fiecare dată când o comandă intră în acea fază.
4. Pentru actualizarea după statusul curierului, instalați `deltatech_delivery_status` și conectorul de
   curier folosit.

## 6. Flux de utilizare

### Pasul 1 — Trimiterea ofertei

**Vânzări → Comenzi → Oferte**, creați o ofertă și apăsați **Trimite prin e-mail**. La trimitere, oferta
trece în prima fază bifată **Send Email** cu secvență mai mare decât faza curentă. Faza apare ca etichetă
colorată în coloana **Phase** din lista de oferte și în formularul comenzii, în primul grup de câmpuri.

### Pasul 2 — Confirmarea comenzii

Apăsați **Confirmă**. Comanda trece în faza bifată **Confirmed**. Invers funcționează la fel: dacă
operatorul alege manual, pe o ofertă încă neconfirmată, o fază bifată **Confirmed**, comanda se
confirmă automat — faza și starea comenzii rămân coerente.

### Pasul 3 — Validarea livrării

Din comandă, butonul **Livrare** → **Validează**. Dacă tipul de operație al livrării are o **Phase**
setată (vezi configurarea), comanda trece direct în acea fază, indiferent de ordine.

### Pasul 4 — Statusul curierului

Când conectorul de curier actualizează statusul livrării, comanda urmează automat:

| Status livrare | Faza căutată | Respectă ordinea fazelor? |
|---|---|---|
| AWB generat (preavizare) | **Pre Advice** | da — doar spre o fază ulterioară |
| Ridicat / în tranzit / în depozit / în livrare | **Shipped** | nu — se setează oricum |
| Livrat | **Delivered** | da |
| Refuzat | **Refused** | nu — se setează oricum |

### Pasul 5 — Facturarea

Creați factura din comandă și **validați-o**. În momentul validării, dacă întreaga comandă a ajuns
**complet facturată**, ea trece în faza bifată **Invoiced**. O factură parțială nu mută comanda.
Pe 19.0, utilizatorul care validează factura trebuie să aibă cel puțin **Vânzări: Utilizator**: la
validare se citesc fazele comenzii, iar fără acest drept validarea se oprește cu o eroare de acces.

### Pasul 6 — Anularea

**Anulează** pe comandă o mută în faza bifată **Canceled**; alegerea manuală a unei faze **Canceled**
anulează comanda.

### Pasul 7 — Urmărirea comenzilor pe faze

**Vânzări → Comenzi → Comenzi**: coloana **Phase** arată eticheta colorată. Pentru a vedea încărcarea pe
etape:

1. **Găsiți pe ecran** — în căutare, deschideți **Grupează după → Phase**; fiecare grup este o fază,
   cu numărul de comenzi și totalul lor.
2. **Verificați** — comenzile confirmate dar nelivrate nu stau în „Facturată”; comenzile anulate sunt
   toate în „Anulată”; nu există comenzi confirmate fără fază (grupul „Nedefinit”), în afara celor
   create înainte de instalarea modulului.
3. **Treceți mai departe** — filtrați direct o fază scriindu-i numele în căutare și alegând **Căutare
   Phase**, apoi lucrați lista (ex. comenzile „Pregătite” de predat curierului).

### Note de monografie și raportare

Modulul **nu generează note contabile**. Fazele sunt doar etichete pe comandă, utile în listă, în
filtre și în rapoartele de vânzări grupate pe fază.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale_stock` | Livrările comenzii; validarea lor mută faza |
| `deltatech_widget_many2one_badge` | Afișarea fazei ca etichetă colorată |
| `deltatech_delivery_status` | Statusul curierului (preavizare, tranzit, livrat, refuzat) |
| Conectorii de curier (ex. Sameday, Cargus, FAN) | Completează statusul de livrare |
| `payment` | Tranzacțiile încheiate fac ca, la avansare, să fie preferate fazele bifate **Paid** |

**Ce e automat:** trecerea în faze la trimiterea ofertei, confirmare, validarea livrării, statusul
curierului, facturarea completă și anulare; rularea acțiunii server atașate fazei; confirmarea sau
anularea comenzii când se alege manual o fază **Confirmed** / **Canceled**.

**Ce rămâne manual:** definirea fazelor și a ordinii lor; fazele fără bifă de eveniment (ex.
„Pregătită”), dacă nu sunt legate de un tip de operație; corecturile de fază.

## 8. Verificări pentru consultant

- [ ] Fazele au secvențe în ordinea fluxului real; o fază bifată **Send Email** are secvență mai mică
      decât cea bifată **Confirmed**.
- [ ] Trimiterea ofertei pe e-mail o mută în faza **Send Email**.
- [ ] **Confirmă** mută comanda în faza **Confirmed**; alegerea manuală a fazei **Confirmed** pe o
      ofertă o confirmă.
- [ ] Validarea livrării pe un tip de operație cu **Phase** setată mută comanda în acea fază.
- [ ] O factură parțială **nu** schimbă faza; factura care completează comanda o mută în **Invoiced**.
- [ ] Contabilul care validează facturile are și **Vânzări: Utilizator** (altfel validarea dă eroare de
      acces).
- [ ] **Anulează** mută comanda în **Canceled**.
- [ ] Acțiunea server a unei faze rulează la intrarea comenzii în fază.
- [ ] Gruparea **Phase** din lista de comenzi arată numărul corect de comenzi pe fiecare fază.
- [ ] Un **Utilizator vânzări** vede fazele, dar nu le poate crea sau modifica în configurare.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Faza nu se schimbă la confirmare sau trimitere | Nu există fază cu bifa corespunzătoare, sau ea are secvență mai mică decât faza curentă | Bifați evenimentul pe fază și verificați ordinea |
| Faza nu se schimbă la validarea livrării | Tipul de operație nu are **Phase** setată | Completați **Phase** pe tipul de operație |
| Faza „sare” înapoi la validarea livrării | Faza tipului de operație se aplică indiferent de ordine | Alegeți pe tipul de operație o fază ulterioară celei curente |
| Faza nu trece în **Invoiced** după validarea facturii | Comanda nu e încă complet facturată | Facturați restul sau acceptați faza curentă |
| „The order was not invoiced” la alegerea manuală a fazei **Invoiced** pe o comandă facturată | Condiția din verificarea manuală este inversată — problemă cunoscută (dhongu/deltatech#3533) | Lăsați faza **Invoiced** să fie setată automat de validarea facturii |
| Eroare de acces la validarea facturii unei comenzi, pentru un contabil | Pe 19.0 fazele se citesc cu drepturile utilizatorului, iar contabilul nu are drept pe Vânzări | Dați-i **Vânzări: Utilizator**; pe 20.0 fazele se citesc fără această condiție |
| Eroare de drepturi la crearea unei faze | Utilizatorul nu e **Administrator** vânzări | Fazele le configurează managerul de vânzări |

## 10. Capturi de ecran

Fișa este **doar text**, fără capturi. Dacă se vor adăuga, capturile planificate, în ordinea pașilor:

| # | Fișier planificat | Conținut |
|---|---|---|
| 1 | `01_configurare_faze.png` | Lista **Sale Order phase** cu fazele și bifele de eveniment |
| 2 | `02_tip_operatie_faza.png` | Tipul de operație **Livrări** cu câmpul **Phase** |
| 3 | `03_comanda_faza.png` | Comanda confirmată cu eticheta **Phase** |
| 4 | `04_lista_grupata_faze.png` | Lista de comenzi grupată după **Phase** |

Generarea lor se face cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în română.

## 11. Observații pentru manual

Explicați în manual diferența dintre **starea** comenzii (standard Odoo, cu efect asupra documentelor)
și **faza** ei (etichetă internă, configurabilă): operatorii tind să le confunde. Insistați pe
**ordinea fazelor** — avansarea automată merge doar înainte, cu excepția expedierii, refuzului și a
fazei setate de tipul de operație, care se aplică oricum. Precizați că alegerea manuală a unei faze
**Confirmed** sau **Canceled** are efect real asupra comenzii (o confirmă / o anulează), deci nu e doar o
etichetă. Denumirile din meniul de configurare și ale bifelor apar în engleză, pentru că traducerea
română a modulului nu este completă.
