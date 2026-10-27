# Fișă Modul: Costul produselor de tip kit pe comanda de vânzare

**Modul:** `deltatech_kit_price`
**Utilizator principal:** Manager vânzări, controller / analist de marjă, consultant la implementare
**Prioritate:** 🟡 Medie (esențial la companiile care vând pachete — kituri — și urmăresc marja pe comandă)

---

## 1. Scop business

Un **kit** este un produs vândut ca unul singur, dar compus din alte produse (ex. „Set baie” = cadă +
baterie + sifon). În Odoo, kitul are o listă de materiale de tip **Set** (Kit): la livrare ies din stoc
componentele, nu kitul. Kitul însuși nu are un cost propriu, așa că marja calculată pe comanda de
vânzare iese greșit — de obicei egală cu toată valoarea vânzării.

Modulul calculează **costul liniei de comandă** pentru un kit ca **suma costurilor componentelor**, după
cantitățile din lista de materiale. Marja comenzii reflectă astfel costul real al pachetului vândut.

## 2. Bază legală și context

Modul de calcul comercial, fără temei fiscal propriu. Costul afișat pe linia de vânzare servește la
analiza marjei; **nu** este costul contabil al ieșirii din stoc. Costul contabil al mărfii vândute se
înregistrează, ca în standard, la livrarea componentelor (evaluarea stocului fiecărei componente).

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Responsabil produse / producție | Definește lista de materiale de tip **Set** și costurile componentelor |
| Operator vânzări | Adaugă kitul pe comandă; costul se calculează automat |
| Manager vânzări / controller | Urmărește marja pe linii și pe comandă |

Coloanele de cost și marjă ale liniilor sunt ascunse implicit în Odoo 20: se afișează din selectorul
de coloane al liniilor de comandă (pictograma din capătul antetului). Roluri recomandate la testare:
**Vânzări: Administrator** și **Producție: Utilizator**.

## 4. Conturi și date implicate

Modulul nu postează note contabile. Date folosite:

- **Lista de materiale** a kitului, de tip **Set**, cu componentele și cantitățile lor;
- **Costul** fiecărei componente (câmpul **Cost** de pe produs);
- **Unitatea de măsură** și **moneda** liniei de comandă.

Date minime pentru demo: componenta A cu cost 10 lei, componenta B cu cost 20 lei, kitul „Set” cu lista
de materiale de tip Kit = 1 × A + 2 × B. Costul kitului pe comandă: 1 × 10 + 2 × 20 = **50 lei**.

## 5. Configurare inițială

1. Instalați **Producție** (lista de materiale de tip Set e disponibilă și fără ordine de producție).
2. Completați **Cost** pe fiecare componentă (fila **Informații generale** a produsului).
3. **Producție → Produse → Liste de materiale → Nou**: alegeți kitul la **Produs**, setați **Tip LdM** pe
   **Set** și adăugați componentele cu cantitățile lor.
4. Pentru kituri cu variante: lista de materiale poate fi definită pe o variantă anume sau pe șablonul
   produsului (valabilă pentru toate variantele). Modulul o caută întâi pe cea a variantei, apoi pe cea a
   șablonului.

## 6. Flux de utilizare

### Pasul 1 — Adăugarea kitului pe comandă

**Vânzări → Comenzi → Oferte → Nou**, alegeți clientul și adăugați pe o linie kitul „Set”, cantitate 1.
Afișați din selectorul de coloane al liniilor coloanele **Unit Cost**, **Marja** și **Marjă (%)**.
Coloana **Unit Cost** a liniei se completează automat cu **50 lei** — suma costurilor componentelor.

### Pasul 2 — Verificarea marjei

1. **Găsiți pe ecran** — pe linia kitului, coloanele **Unit Cost**, **Marja** și **Marjă (%)**; sub
   linii, totalul marjei comenzii.
2. **Verificați** — **Unit Cost** = suma (cantitate componentă × cost componentă) din lista de materiale;
   marja liniei = subtotal fără TVA − cost × cantitate; marja nu este egală cu toată valoarea vânzării
   (simptomul fără modul).
3. **Treceți mai departe** — confirmați comanda; marja rămâne disponibilă în **Raportare → Vânzări**.

### Pasul 3 — Unitate de măsură și monedă diferite

Dacă linia e vândută într-o altă unitate (ex. **Duzină** în loc de **Bucăți**), costul se convertește
în unitatea liniei: 12 × 50 = 600 lei. Dacă comanda este în altă monedă (listă de prețuri în EUR),
costul se convertește la cursul zilei în moneda comenzii.

### Note de monografie și raportare

Modulul **nu generează note contabile**. La livrare, ies din stoc componentele și, pe evaluare automată,
Odoo înregistrează standard costul mărfurilor vândute pe fiecare componentă (ex. **607 = 371** pentru
mărfuri), la costul de stoc al fiecăreia. Costul de pe linia de vânzare este o estimare pentru marjă și
poate diferi de costul contabil al ieșirii dacă evaluarea componentelor este FIFO sau medie ponderată.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale_margin` | Coloanele de cost și marjă pe comandă |
| `mrp` | Listele de materiale de tip Kit |
| `mrp_account` | Calculul costului din lista de materiale |

**Ce e automat:** costul liniei de kit, la adăugarea liniei și la schimbarea produsului, cantității sau
unității de măsură; conversia în unitatea și moneda liniei.

**Ce rămâne manual:** întreținerea costurilor componentelor și a listei de materiale.

## 8. Verificări pentru consultant

- [ ] Kit cu 1 × A (10 lei) + 2 × B (20 lei): costul liniei este **50 lei**.
- [ ] Un produs obișnuit (fără listă de materiale) păstrează costul propriu de pe produs.
- [ ] Lista de materiale definită doar pe șablon este folosită pentru variantă.
- [ ] Linia vândută la **Duzină** are costul 600 lei.
- [ ] Comanda în EUR are costul convertit la cursul monedei.
- [ ] Marja comenzii nu mai este egală cu toată valoarea vânzării.
- [ ] Un produs cu listă de materiale de tip **Fabrică acest produs** (nu Set) nu este recalculat de modul.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Costul kitului este 0 | Componentele nu au **Cost** completat | Completați costul componentelor |
| Costul nu se schimbă după modificarea costului unei componente | Costul liniei se calculează la adăugarea sau modificarea liniei | Reintroduceți cantitatea pe linie sau creați o linie nouă |
| Costul kitului este cel de pe produs, nu suma componentelor | Lista de materiale nu e de tip **Set** sau este pe altă variantă | Setați **Tip LdM** = **Set** pe variantă sau pe șablon |
| Coloana **Unit Cost** nu apare | Coloana este ascunsă implicit | Afișați-o din selectorul de coloane al liniilor |

## 10. Capturi de ecran

Fișa este **doar text**, fără capturi. Dacă se vor adăuga, capturile planificate, în ordinea pașilor:

| # | Fișier planificat | Conținut |
|---|---|---|
| 1 | `01_lista_materiale_kit.png` | Lista de materiale de tip **Set** cu componentele |
| 2 | `02_comanda_cost_kit.png` | Comanda cu linia de kit, **Unit Cost** 50 lei și marja |

Generarea lor se face cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în română.

## 11. Observații pentru manual

Explicați de ce kitul nu are cost propriu (nu intră în stoc ca atare) și că modulul doar **calculează**
costul pentru marjă — nu schimbă costul contabil. Recomandați clientului să țină la zi costurile
componentelor: marja kitului este atât de corectă cât sunt ele. Precizați că lista de materiale trebuie
să fie de tip **Set**; o listă de tip **Fabrică acest produs** descrie un produs fabricat, cu cost propriu, și nu
este luată în calcul.
