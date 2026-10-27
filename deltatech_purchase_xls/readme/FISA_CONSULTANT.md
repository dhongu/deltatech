# Fișă Modul: Import și export al liniilor comenzii de achiziție din / în Excel

**Modul:** `deltatech_purchase_xls`
**Utilizator principal:** Operator achiziții
**Prioritate:** 🟡 Medie (accelerează comenzile lungi; fluxul standard rămâne disponibil)

---

## 1. Scop business

Furnizorii trimit des oferta sau lista de produse ca fișier Excel, cu sute de rânduri. Introducerea
manuală a liniilor pe comanda de achiziție durează și produce greșeli. Modulul
`deltatech_purchase_xls` permite:

- **importul liniilor** dintr-un fișier Excel (`.xlsx`) într-o cerere de ofertă, cu identificarea
  produselor după codul furnizorului (sau codul intern) și, opțional, crearea produselor lipsă;
- **exportul liniilor** unei comenzi (sau ale mai multor comenzi) într-un fișier Excel, cu codul și
  denumirea furnizorului, pentru a fi trimis furnizorului sau prelucrat în afara Odoo;
- o listă separată a **liniilor comenzii** (butonul „Order lines”), din care liniile existente pot fi
  actualizate cu importul standard Odoo.

## 2. Bază legală și context

Nu există temei legal — este un instrument operațional de introducere și extragere a datelor pe
comenzile de achiziție.

## 3. Utilizatori și roluri

Operator achiziții (utilizator intern cu drept de lucru pe comenzile de achiziție).

Roluri recomandate pentru testare:
- Utilizator achiziții: importă liniile într-o cerere de ofertă, exportă liniile în Excel
- Administrator funcțional: verifică produsele create automat și prețurile de furnizor generate

## 4. Conturi și date implicate

Modulul nu generează note contabile și nu folosește conturi.

Date minime pentru demo:
- un furnizor cu prețuri de furnizor pe produse, cu **Cod produs furnizor** completat
- câteva produse cu **Referință internă** (cod intern)
- o cerere de ofertă **în starea „CdO”** (netrimisă, neconfirmată) pentru acel furnizor
- un fișier `.xlsx` cu liniile; formatul implicit are coloanele, în ordine: cod furnizor, cod intern,
  denumire, cantitate, preț, unitate de măsură (exact formatul produs de export)

## 5. Configurare inițială

1. Instalați modulul `deltatech_purchase_xls` (depinde de `purchase_stock`).
2. Completați **Cod produs furnizor** pe prețurile furnizorului (**Achiziții → Produse → Produse**,
   tab **Achiziție**) — importul caută produsul în primul rând după acest cod, doar printre prețurile
   furnizorului comenzii și ale companiei comenzii.
3. Nu sunt necesare meniuri sau setări noi.

## 6. Flux de utilizare

### Pasul 1 — Pregătirea fișierului Excel

Pregătiți fișierul `.xlsx` cu datele pe prima foaie. Ordinea coloanelor trebuie să corespundă
câmpului **Campuri** din fereastra de import; implicit:
`product_code,default_code,product_name,quantity,price,uom_name` (cod furnizor, cod intern,
denumire, cantitate, preț, unitate de măsură). Rândurile fără cod furnizor (prima coloană) sunt
ignorate. Cel mai simplu este să porniți de la un fișier exportat de modul (pasul 5).

### Pasul 2 — Deschiderea importului pe cererea de ofertă

Accesați **Achiziții → Comenzi → Cereri de ofertă** și deschideți o cerere de ofertă în starea
„CdO”. Din meniul **Acțiuni** (rotița din antetul formularului) alegeți **Import linie achizitie**.
Se deschide fereastra **Import linii achizitie**. Dacă cererea a fost deja trimisă sau confirmată,
apare mesajul „Comanda este in starea …” și importul nu este permis.

### Pasul 3 — Alegerea fișierului și a opțiunilor

În fereastră completați:
- **File** — fișierul `.xlsx`;
- **Campuri** — lista coloanelor, în ordinea din fișier (lăsați valoarea implicită pentru un fișier
  exportat de modul; scoateți `default_code` dacă fișierul are 5 coloane);
- **Rand antet** — bifați dacă primul rând conține titlurile coloanelor (se sare peste el);
- **Creare produs lipsa** — bifați pentru a crea automat produsele care nu se găsesc (produs
  stocabil, cu prețul de furnizor și codul furnizorului din fișier); nebifat, un cod negăsit oprește
  importul;
- **Is amount** — bifați dacă coloana de preț conține **valoarea totală** a liniei; prețul unitar se
  calculează ca valoare / cantitate;
- **Cauta dupa cod intern** — bifați pentru a căuta și după **Referința internă** a produsului când
  codul furnizorului nu e găsit.

Apăsați **Aplica**.

### Pasul 4 — Verificarea liniilor importate

Fereastra se închide, iar liniile apar pe cererea de ofertă, cu produsul, cantitatea, prețul unitar,
unitatea de măsură și taxele de achiziție ale produsului. Dacă denumirea din fișier diferă de numele
produsului, ea apare ca descriere a liniei.
1. **Găsiți** liniile noi în tabul **Produse** al cererii de ofertă.
2. **Verificați** numărul de linii față de numărul de rânduri cu cod din fișier, prețul unitar (mai
   ales dacă ați folosit **Is amount**) și unitatea de măsură; verificați produsele create automat
   (nume, unitate de măsură).
3. **Treceți mai departe** — trimiteți sau confirmați cererea de ofertă ca de obicei.

### Pasul 5 — Exportul liniilor în Excel

Pe formularul comenzii (sau în lista de comenzi, după ce bifați una sau mai multe comenzi) deschideți
meniul **Tipăriți** și alegeți **Export linii achizitie**. În fereastra **Export linie achizitie**
apăsați **Aplica**. Apare mesajul „Export complet” cu fișierul `purchase_order.xlsx`, pe care îl
descărcați din link; închideți fereastra cu **Exit**.

Fișierul are foaia „Order Lines” cu coloanele **Code** (codul furnizorului), **Internal Code**
(referința internă), **Name** (denumirea de la furnizor, dacă există, altfel numele produsului),
**Qty**, **Price** și **Unit of Measure**, câte un rând pentru fiecare linie a fiecărei comenzi
selectate.
1. **Găsiți** în fișier rândurile fiecărei comenzi exportate.
2. **Verificați** că numărul de rânduri este egal cu numărul de linii al comenzilor și că acolo unde
   furnizorul are cod propriu, coloana **Code** este completată.
3. **Treceți mai departe** — trimiteți fișierul furnizorului sau folosiți-l ca model pentru un import.

### Pasul 6 — Actualizarea liniilor existente din lista „Order lines”

Pe formularul comenzii apăsați butonul inteligent **Order lines**. Se deschide lista liniilor comenzii
(**Comandă de achiziție**, **Produs**, cantitate, **Preț unitar**). Din această listă puteți folosi
importul standard Odoo (din rotița listei) pentru a actualiza liniile:
- dacă comanda are deja linii, fiecare rând din fișier este asociat liniei existente cu același
  produs (produsul se recunoaște după codul dintre paranteze drepte `[COD]` sau după nume), iar
  rândurile cu produse care nu sunt pe comandă sunt ignorate;
- dacă comanda nu are linii, rândurile se adaugă ca linii noi pe comandă.

Atenție: în versiunea curentă, un rând cu produs necunoscut poate face ca rândul următor să fie
sărit (vezi [dhongu/deltatech#3819](https://github.com/dhongu/deltatech/issues/3819)); verificați
liniile după import.

### Note de monografie și raportare

Modulul nu generează note contabile. Liniile importate sunt linii obișnuite de comandă; contabilizarea
apare doar la recepție și la factura furnizorului, conform fluxului standard de achiziții.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `purchase_stock` | comanda de achiziție, liniile și prețurile furnizorului | dependență (manifest) |
| Importul standard Odoo | actualizarea liniilor din lista „Order lines” | folosit indirect |

Ce este automat: identificarea produselor după codul furnizorului (sau codul intern), crearea
produselor lipsă (dacă e bifat), calculul prețului unitar din valoare, taxele de achiziție pe linii,
exportul cu codurile și denumirile furnizorului.
Ce rămâne manual: pregătirea fișierului, alegerea opțiunilor, verificarea liniilor și a produselor
create.

## 8. Verificări pentru consultant

- [ ] **Import linie achizitie** apare în meniul **Acțiuni** al cererii de ofertă.
- [ ] Pe o comandă trimisă sau confirmată, importul este refuzat cu „Comanda este in starea …”.
- [ ] Un fișier exportat de modul se poate reimporta cu valoarea implicită a câmpului **Campuri**.
- [ ] Cu **Rand antet** bifat, primul rând nu devine linie de comandă.
- [ ] Produsele se găsesc după codul furnizorului comenzii; cu **Cauta dupa cod intern**, și după
      referința internă.
- [ ] Un cod negăsit oprește importul cu „Produsul … nu a fost gasit”; cu **Creare produs lipsa**,
      produsul se creează, cu preț de furnizor.
- [ ] Cu **Is amount**, prețul unitar = valoare / cantitate.
- [ ] **Export linii achizitie** (meniul **Tipăriți**) produce `purchase_order.xlsx` cu cele 6
      coloane, pentru una sau mai multe comenzi.
- [ ] Butonul **Order lines** deschide lista liniilor comenzii.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| „Comanda este in starea …” | Importul se face doar pe cereri de ofertă în starea „CdO” | Importați înainte de trimitere/confirmare sau duplicați comanda |
| „Produsul … nu a fost gasit” | Codul nu există pe prețurile furnizorului comenzii (nici ca referință internă, dacă e bifată căutarea) | Completați **Cod produs furnizor** sau bifați **Creare produs lipsa** / **Cauta dupa cod intern** |
| „The supplier code … matches several products …” | Același cod de furnizor e pe prețuri de furnizor ale mai multor variante | Setați varianta de produs pe prețul furnizorului |
| „Produsul … nu are UM …” | Unitatea de măsură din fișier există, dar diferă de unitatea produsului | Corectați unitatea în fișier sau lăsați coloana goală |
| „Invalid format fisier” | Coloanele din fișier nu corespund câmpului **Campuri** | Aliniați lista de câmpuri cu ordinea coloanelor |
| Prețuri unitare prea mari/mici | Coloana de preț conține valoarea liniei, dar **Is amount** nu e bifat (sau invers) | Reimportați cu opțiunea corectă |
| Fișier `.xls` (format vechi) nu se citește | Se citesc doar fișiere `.xlsx` | Salvați fișierul ca `.xlsx` |

## 10. Capturi de ecran

Fișa este **doar text** — nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele prin
etichetele lor reale din interfață. Dacă se decide ulterior completarea cu capturi, se rulează
skill-ul `fisa-screenshots`, care generează imaginile din `tests/test_screenshots.py` (mixinul
`ScreenshotCase`), în română, iar secțiunile 6 și 10 se actualizează în consecință.

## 11. Observații pentru manual

Prezentați exportul și importul ca pereche: fișierul exportat este și modelul de import. Subliniați
că importul se face doar pe cereri de ofertă netrimise și că asocierea sigură se face după **Codul
produsului furnizor**. Explicați opțiunea **Is amount** pentru ofertele care dau doar valoarea pe
linie. Etichetele ferestrelor apar în interfață fără diacritice („Import linie achizitie”, „Campuri”,
„Rand antet”), iar câteva sunt netraduse („File”, „Is amount”, „Order lines”, „Exit”) — păstrați-le
așa în manual până la corectarea traducerilor.
