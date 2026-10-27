# Fișă Modul: Comandă în valută, factură în moneda jurnalului

**Modul:** `deltatech_sale_currency`
**Utilizator principal:** Agent de vânzări și contabil (facturare clienți)
**Prioritate:** 🔴 Ridicată (schimbă moneda facturilor emise din comenzi)

---

## 1. Scop business

Multe firme negociază și ofertează în valută (EUR, USD), dar facturează în lei. În Odoo standard,
factura creată dintr-o comandă preia moneda comenzii, deci o comandă în EUR dă o factură în EUR.
Modulul schimbă acest comportament: **factura primește moneda jurnalului de vânzări** al comenzii
(sau, dacă jurnalul nu are monedă, moneda companiei, adică lei), iar **prețurile se convertesc** din
moneda comenzii în moneda facturii, la cursul zilei. Când se schimbă data facturii, prețurile se
reconvertesc la cursul noii date.

## 2. Bază legală și context

- **Legea contabilității nr. 82/1991** — evidența contabilă se ține în limba română și în moneda
  națională; factura în lei evită diferențele de curs pe creanța în valută.
- **Codul fiscal (Legea 227/2015), art. 290** — pentru determinarea bazei de impozitare a TVA în cazul
  sumelor exprimate în valută, se folosește cursul de schimb de la data exigibilității taxei.

Modulul folosește cursul înregistrat în Odoo pentru data facturii (în practică cursul BNR, încărcat
automat); actualizarea cursurilor rămâne în sarcina configurării monedelor.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Agent de vânzări | Creează comanda în valută (listă de prețuri în EUR/USD) și o confirmă |
| Facturare / contabil | Creează factura din comandă, verifică moneda și prețurile, stabilește data facturii și o validează |
| Administrator contabilitate | Configurează moneda jurnalelor de vânzări și cursurile valutare |

Modulul nu adaugă grupuri. Roluri recomandate pentru testare: un agent de vânzări și un utilizator
cu drept de facturare.

## 4. Conturi și date implicate

Modulul nu adaugă conturi; factura folosește conturile standard ale clientului și produselor. Date
minime pentru demo:

- moneda EUR activă, cu cursuri pentru ziua comenzii și pentru ziua facturii (ex. 4,97 și 4,98 lei);
- o listă de prețuri în EUR;
- un jurnal de vânzări fără monedă (factura va fi în lei) sau cu monedă proprie;
- un client și un produs cu preț de vânzare.

## 5. Configurare inițială

1. Instalați modulul `deltatech_sale_currency` (depinde de `sale` și `account`).
2. **Contabilitate → Configurare → Monede**: activați valuta folosită pe comenzi și verificați că are
   cursuri (actualizarea automată a cursurilor BNR, dacă este folosită).
3. **Contabilitate → Configurare → Jurnale**: pe jurnalul de vânzări folosit, câmpul **Monedă** decide
   moneda facturii; lăsat gol, factura va fi în moneda companiei.
4. **Vânzări → Produse → Liste de prețuri**: creați lista de prețuri în valută.

## 6. Flux de utilizare

### Pasul 1 — Comanda în valută

Agentul creează oferta în **Vânzări → Comenzi → Oferte**, alege clientul și lista de prețuri în EUR.
Prețurile liniilor sunt în EUR. Jurnalul de facturare al comenzii se vede în pagina **Alte informații**,
câmpul **Jurnal** (vizibil în modul dezvoltator); implicit este jurnalul de vânzări cu cea mai mică
secvență. Agentul confirmă comanda cu **Confirmă**.

### Pasul 2 — Crearea facturii

Pe comanda confirmată (și livrată, dacă politica de facturare o cere), utilizatorul apasă **Creează
factura** (*Create Invoice*) și alege **Factură obișnuită**.

1. **Găsește pe ecran** — pe factura nouă: câmpul **Monedă** și coloana **Preț** pe linii.
2. **Verifică** — moneda este cea a jurnalului (sau lei, dacă jurnalul nu are monedă), nu EUR; prețul
   fiecărei linii = prețul din comandă × cursul zilei curente (ex. 100 EUR × 4,97 = 497,00 lei);
   cantitățile și taxele sunt cele din comandă.
3. **Treci mai departe** — completați data facturii (Pasul 3), apoi validați.

### Pasul 3 — Data facturii și reconversia

Utilizatorul completează **Data facturii** (sau schimbă **Moneda**). La schimbare, prețurile liniilor
provenite din comandă se recalculează pornind din prețul din comandă, la cursul datei facturii
(ex. cu data de mâine și cursul 4,98: 100 EUR → 498,00 lei). Dacă unitatea de măsură a liniei de
factură diferă de cea din comandă, prețul se convertește întâi în unitatea facturii.

Liniile adăugate manual pe factură (fără legătură cu o comandă) nu sunt reconvertite: prețul lor
rămâne cel introdus.

Verificați prețurile după fiecare schimbare de dată, apoi apăsați **Confirmă** pentru a posta factura.

### Pasul 4 — Avansuri

La facturarea unei comenzi cu avans (factură de avans emisă în lei pe o comandă în EUR), suma
avansului deja facturat se reconvertește în moneda comenzii, la cursul de la data facturii de avans,
astfel încât la factura finală avansul se deduce corect.

### Note de monografie și raportare

Factura postată este în moneda facturii (lei), cu nota standard:

| Dr | Cr | Sumă |
|---|---|---|
| 4111 Clienți | 707 Venituri din vânzarea mărfurilor / 704 Venituri din servicii | baza în lei (preț convertit × cantitate) |
| 4111 Clienți | 4427 TVA colectată | TVA în lei |

Pentru că factura este în lei, creanța nu generează diferențe de curs la încasare (665/765).

## 7. Legături cu alte module / declarații

| Modul / declarație | Rol |
|---|---|
| `sale` | comanda, lista de prețuri în valută, crearea facturii |
| `account` | jurnalul de vânzări, factura, cursurile valutare |
| Cursuri BNR (localizarea RO) | sursa cursului folosit la conversie |
| Jurnalul de vânzări / D300 / D394 / e-Factura | preiau factura în lei, cu valorile convertite |

**Ce e automat:** moneda facturii după jurnal, conversia prețurilor la creare, reconversia la
schimbarea datei facturii, recalcularea avansului.

**Ce rămâne manual:** alegerea jurnalului și a monedei lui; încărcarea cursurilor; verificarea
prețurilor înainte de validare.

## 8. Verificări pentru consultant

- [ ] O comandă în EUR, facturată pe un jurnal fără monedă, dă o factură în lei.
- [ ] Pe un jurnal cu monedă proprie (ex. USD), factura este în moneda jurnalului.
- [ ] Prețul pe factură = preț comandă × cursul zilei la creare.
- [ ] Schimbarea **Datei facturii** recalculează prețurile la cursul noii date.
- [ ] O linie în altă unitate de măsură decât în comandă primește prețul convertit în unitatea facturii.
- [ ] O comandă în aceeași monedă cu jurnalul nu are prețuri modificate.
- [ ] La factura finală, avansul în lei se deduce corect din comanda în EUR.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `You cannot have multiple currencies in the same invoice line.` | O linie de factură provine din linii de comandă în monede diferite | Facturați separat comenzile în monede diferite |
| Prețuri neconvertite / curs 1 | Lipsește cursul valutei pentru data facturii | Încărcați cursul pentru data respectivă și schimbați din nou data |
| Factura e în EUR, nu în lei | Jurnalul comenzii are moneda EUR | Alegeți pe comandă un jurnal fără monedă sau în lei |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Capturile
pentru comanda în EUR și factura în lei (pașii 1–3) se pot genera ulterior cu skill-ul
`fisa-screenshots`.

## 11. Observații pentru manual

- De subliniat că modulul se aplică tuturor facturilor create din comenzi: o comandă în EUR va fi
  facturată în lei, dacă jurnalul nu are monedă.
- Ordinea recomandată: completați **Data facturii** înainte de validare, ca prețurile să fie la cursul
  zilei facturii.
- Prețurile modificate manual pe liniile facturii care provin din comandă se pierd la o nouă schimbare a datei facturii
  (reconversia pornește mereu din prețul comenzii).
