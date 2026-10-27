# Fișă Modul: Foi de parcurs, alimentări și carduri de combustibil

**Modul:** `deltatech_fleet`
**Utilizator principal:** Responsabil parc auto (foi de parcurs, alimentări); manager flotă (date de bază, rapoarte)
**Prioritate:** 🟡 Medie (evidența consumului și a kilometrilor parcurși, baza justificării cheltuielilor cu combustibilul)

---

## 1. Scop business

Aplicația Flotă din Odoo ține evidența vehiculelor, a contractelor și a serviciilor, dar nu are foi de
parcurs. Modulul adaugă:

- **foaia de parcurs** pe vehicul și perioadă, cu traseele parcurse, alimentările, kilometrajul la
  început și la sfârșit, distanța totală, consumul normat și nivelul de combustibil din rezervor;
  foaia se tipărește ca PDF;
- **alimentările** (jurnale de combustibil), legate de vehicul, de cardul de combustibil și de foaia de
  parcurs;
- **cardurile de combustibil**, alocate vehiculelor;
- **traseele** între locații, cu distanță și durată, și crearea dintr-un clic a traseului invers;
- date suplimentare pe vehicul: indicativ, categorie, serie motor, capacitate rezervor, consumuri medii,
  firma proprietară / contractantă / utilizatoare;
- raportul **costului pe kilometru** pe vehicul și perioadă.

## 2. Bază legală și context

Foaia de parcurs este documentul justificativ uzual pentru deductibilitatea cheltuielilor cu
combustibilul ale vehiculelor folosite în activitatea economică (Codul fiscal, Legea 227/2015, art. 25
pentru impozitul pe profit și art. 298 pentru TVA, cu normele de aplicare). Modulul ține evidența
operativă (trasee, kilometri, litri, consum normat); conformitatea formularului cu cerințele firmei și
ale auditorului fiscal se verifică de consultant la implementare.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Utilizator Flotă (*Fleet: Officer*) | Înregistrează alimentările și locațiile vehiculelor |
| Manager Flotă (*Fleet: Administrator*) | Completează foile de parcurs și traseele parcurse, întreține datele de bază (trasee, locații, carburanți, scopuri, carduri, categorii), folosește butonul **Foi parcurs** din fișa vehiculului și raportul **Distance Report** |

Atenție: foile de parcurs, traseele parcurse și datele de bază (trasee, locații, carburanți, scopuri,
carduri, categorii) au drepturi doar pentru **Manager Flotă**; un utilizator Flotă vede meniurile
**Foi parcurs**, **Traseu parcurs** și **Date de bază**, dar nu poate deschide înregistrările. Pentru
testare folosiți un **Manager Flotă**.

## 4. Conturi și date implicate

Modulul nu generează note contabile. Costul alimentărilor intră în costurile vehiculului din aplicația
Flotă (tipul de serviciu **Fuel**), nu în contabilitate; înregistrarea contabilă a facturilor de
combustibil (de exemplu contul 6022 „Cheltuieli privind combustibilii” și TVA deductibilă 4426) se
face separat, din factura furnizorului.

Date create la instalare: tipul de serviciu **Fuel**, secvența foilor de parcurs (`MS/00010`, pas 10),
categoriile de vehicul M1–M3, N1–N3, O1–O4 și locația **Home**.

Date minime pentru demo: un vehicul cu kilometraj, consum mediu și categorie; două locații; un traseu
între ele (cu traseul invers); un card de combustibil; o alimentare.

## 5. Configurare inițială

1. Instalați modulul `deltatech_fleet` (depinde de `fleet`).
2. Pe vehicul (**Flotă → Flotă → Flotă**), completați:
   - **Vehicle Category** (lângă șofer) și **Engine Serial Number**;
   - fila **Consumption**: **Reservoir capacity**, **Average Consumption** (consumul normat, l/100 km,
     folosit la calculul consumului pe trasee), consumurile urban / extraurban, **Average Speed**;
   - fila **Allocation**: firma proprietară, firma contractantă, firma utilizatoare, modul de alocare,
     divizia, scopul;
   - fila **Cards**: cardurile de combustibil ale vehiculului.
3. Datele de bază, în **Flotă → Flotă → Date de bază** (*Master data*):
   - **Locații** — locurile între care circulă vehiculele (tip: Other, Partner, Station);
   - **Trasee** — **From**, **To**, distanța (**Distance**, plus distanțele pe categorii de drum
     **Dist C1/C2/C3**), durata (**Duration**, ore:minute); butonul **(creare)** de lângă **Reverse
     route** creează traseul invers;
   - **Carburanți** — denumire și tip (Gasoline / Diesel);
   - **Scopul** (*Scope*) — scopurile deplasărilor;
   - **Card** — seria cardului (unică), emitentul, vehiculele.
4. Categoriile de vehicul se completează în **Flotă → Configurare → Categorie vehicul**.

## 6. Flux de utilizare

### Pasul 1 — Înregistrarea alimentărilor

**Flotă → Flotă → Vehicles Fuel Logs**, butonul **Nou**. În formular completați:

- grupul **Vehicle Details**: vehiculul, **Date Time** (obligatoriu), cardul, tipul de serviciu
  (**Fuel**); câmpul **Level Reservoir** arată nivelul calculat al rezervorului la momentul alimentării;
- grupul **Refueling Details**: litrii, prețul pe litru și suma (oricare două o calculează pe a treia),
  **To full** (alimentare până la plin), carburantul și, opțional, foaia de parcurs (sunt propuse doar
  foile vehiculului care cuprind data alimentării);
- grupul **Odometer Details**: kilometrajul la alimentare (se salvează ca citire de kilometraj a
  vehiculului).

Lista alimentărilor este grupată implicit pe vehicul și are și vedere kanban și grafic.

### Pasul 2 — Crearea foii de parcurs

**Flotă → Flotă → Foi parcurs**, butonul **Nou** (sau butonul **Foi parcurs** din fișa vehiculului).
Numărul foii se dă automat (`MS/...`). Alegeți vehiculul: se completează șoferul, șoferul de rezervă,
categoria și consumul mediu. Completați **Date Start** și **Date End**.

Kilometrajul **Odometer Start** / **Odometer End** se citește din citirile de kilometraj ale
vehiculului (ultima citire de la începutul perioadei, prima de după sfârșitul ei) sau se scrie
manual; o valoare scrisă manual devine citire de kilometraj a vehiculului. Butoanele de citire a
kilometrajului (vizibile în stadiul **Draft**) reiau calculul.

### Pasul 3 — Traseele parcurse

În fila **Traseu parcurs** (*Route Log*) adăugați câte un rând pentru fiecare deplasare: la alegerea traseului se
completează distanța, distanțele pe categorii și ora de sfârșit (din durata traseului); ora de început
a unui rând nou continuă de la sfârșitul rândului anterior. Rândurile din zilele de sâmbătă și duminică
apar cu roșu. Coloanele **Distance** și **Equivalence Distance** au total.

Traseele înregistrate separat (**Flotă → Flotă → Traseu parcurs**) pentru vehicul și perioadă se
aduc în foaie cu butonul **Get route log**.

### Pasul 4 — Alimentările din foaie

În fila **Fuel Logs** se adaugă alimentările direct în foaie, sau se aduc cele înregistrate la pasul 1,
pentru vehicul și perioadă, cu butonul **Get fuel log**. Totalurile **Total Liter** și **Total Amount**
apar sub coloane.

### Pasul 5 — Verificarea foii pe ecran

1. **Găsiți pe ecran** — în antetul foii: **Total distance** (suma distanțelor traseelor), **Total
   Liter** și **Total Amount** (alimentările), **Normal Consumption** (consumul normat al traseelor),
   **Level Reservoir Start** și **Level Reservoir End** (nivelul calculat al rezervorului), kilometrajul
   la început și la sfârșit.
2. **Verificați** — **Odometer End** − **Odometer Start** este egal cu **Total distance**; nivelul
   rezervorului la sfârșit este aproximativ nivelul de la început + litrii alimentați − consumul normat;
   niciun traseu nu iese din perioada foii; fiecare alimentare din perioadă este în foaie.
   Totalurile se recalculează la adăugarea sau ștergerea rândurilor, dar **nu** la modificarea
   distanței sau a litrilor unui rând deja salvat (issue dhongu/deltatech#3680): după o astfel de
   modificare, verificați totalurile cu sumele din coloane.
3. **Mai departe** — tipăriți foaia: meniul **Tipăriți → Map Sheet** generează PDF-ul foii, cu antetul
   (vehicul, șofer, perioadă, kilometraj, nivel rezervor), traseele și alimentările.

### Pasul 6 — Confirmarea și închiderea foii

Butonul **Confirm** trece foaia în **In Progress**. Butonul **Done** o închide și marchează alimentările
ei ca terminate; o foaie cu distanța totală zero nu poate fi închisă. Duplicarea unei foi creează foaia
zilei următoare (datele mutate cu o zi, fără alimentări).

### Pasul 7 — Raportul costului pe kilometru

**Flotă → Raportare → Distance Report** (doar Manager Flotă) deschide fereastra cu **Start Date** și
**End Date** (implicit luna curentă). Butonul **Show Report** deschide lista pe vehicule:

1. **Găsiți pe ecran** — coloanele **Vehicle**, **Cost** (costurile de servicii și contracte ale
   vehiculului din raportul de costuri al Flotei, inclusiv alimentările), **Distance** (diferența dintre
   citirile de kilometraj de la capetele perioadei) și **Price** (cost pe kilometru).
2. **Verificați** — vehiculul are citiri de kilometraj înainte și după perioadă (altfel distanța e zero
   și prețul pe km rămâne zero); costul corespunde costurilor vehiculului din **Flotă → Raportare**
   pentru aceleași luni.
3. **Mai departe** — exportați lista în Excel din acțiunile listei, dacă e nevoie.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr). Rapoartele lui sunt operative: PDF-ul foii de parcurs,
lista **Distance Report**, analiza costurilor Flotei (alimentările apar ca servicii de tip **Fuel**)
și graficele foilor și alimentărilor pe vehicul.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `fleet` | Vehiculele, citirile de kilometraj, serviciile (alimentarea moștenește serviciul de vehicul), raportul de costuri |
| `deltatech_fleet_geo` | Coordonatele locațiilor și ale traseelor |
| Contabilitate (în afara modulului) | Factura de combustibil se înregistrează separat, din factura furnizorului |

**Ce e automat:** numerotarea foilor; preluarea șoferilor și a consumului din vehicul; distanța și ora
de sfârșit din traseu; totalurile foii; consumul normat (distanța × consumul mediu / 100); nivelul
rezervorului; citirile de kilometraj create din foaie; costul pe kilometru.

**Ce rămâne manual:** introducerea traseelor și a alimentărilor; legarea alimentărilor de foaie (sau
butoanele **Get**); verificarea kilometrajului; închiderea foii; contabilizarea facturilor de
combustibil.

## 8. Verificări pentru consultant

- [ ] Un Manager Flotă poate crea o foaie de parcurs; numărul foii are prefixul `MS/`.
- [ ] La alegerea vehiculului se completează șoferul, categoria și consumul mediu.
- [ ] La alegerea unui traseu în fila **Traseu parcurs** se completează distanța și ora de sfârșit.
- [ ] **Total distance** este suma distanțelor traseelor, iar **Normal Consumption** = distanța ×
  **Average Consumption** / 100.
- [ ] **Get fuel log** aduce alimentările vehiculului din perioada foii, nelegate de altă foaie.
- [ ] **Get route log** aduce traseele vehiculului din perioada foii, nelegate de altă foaie.
- [ ] **Level Reservoir Start/End** reflectă alimentările minus consumul normat până la acel moment.
- [ ] **Done** este refuzat pentru o foaie fără trasee (distanță zero).
- [ ] PDF-ul **Map Sheet** conține traseele și alimentările foii.
- [ ] O alimentare cu litri și preț pe litru calculează suma.
- [ ] **Distance Report** arată costul și distanța pe vehicul pentru perioada aleasă.
- [ ] Butonul **(creare)** de pe traseu creează traseul invers, cu locațiile inversate.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| *Cannot set done a map sheet which distance equal with zero.* | Foaia nu are trasee sau distanțele sunt zero | Adăugați traseele parcurse înainte de **Done** |
| *Map Sheet end-date (...) must be greater then start-date (...)* | **Date End** este înaintea **Date Start** | Corectați perioada foii |
| *Route end-date must be greater then route begin-date* | Un traseu se termină înainte să înceapă | Corectați orele traseului |
| *The series must be unique !* | Mai există un card cu aceeași serie | Folosiți seria corectă sau arhivați cardul vechi |
| *The Indicative must be unique !* | Indicativul este folosit de alt vehicul | Alegeți alt indicativ |
| *Emptying the odometer value of a vehicle is not allowed.* | Kilometrajul alimentării a fost golit | Completați kilometrajul |
| Eroare de acces la deschiderea foilor de parcurs | Utilizatorul are doar rolul *Fleet: Officer* | Acordați rolul **Manager Flotă** |
| Totalurile foii nu corespund rândurilor | Un rând salvat a fost modificat (issue dhongu/deltatech#3680) | Ștergeți și readăugați rândul, sau corectați după remedierea issue-ului |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`. Capturile
(alimentarea, foaia de parcurs cu filele **Traseu parcurs** și **Fuel Logs**, PDF-ul **Map Sheet**,
fereastra și lista **Distance Report**) se pot genera ulterior cu skill-ul `fisa-screenshots`.

## 11. Observații pentru manual

- Etichetele modulului sunt în mare parte netraduse în română (de exemplu **Fuel Logs**, **Get fuel
  log**, **Distance Report**); manualul le citează în engleză, așa cum apar pe ecran.
- Consumul normat folosește **Average Consumption** al vehiculului la momentul calculului traseului;
  schimbarea consumului pe vehicul nu recalculează foile vechi.
- Nivelul rezervorului este calculat (alimentări minus consum normat), nu măsurat: o alimentare lipsă
  sau un traseu lipsă îl deformează.
- Issue-uri deschise relevante: dhongu/deltatech#3680 (totalurile foii), dhongu/deltatech#3681
  (nivelul rezervorului, accesul pe companie), dhongu/deltatech#3682 (raportul de costuri).
