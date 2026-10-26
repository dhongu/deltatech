# Fișă Modul: Import linii în transferuri și inventar fizic

**Modul:** `deltatech_import_lines_stock` (punte între `deltatech_import_lines` și `stock`)
**Utilizator principal:** Gestionar sau operator de depozit care primește avize și liste de numărătoare în Excel
**Prioritate:** 🟡 Medie (scutește introducerea manuală a recepțiilor și a numărătorilor lungi; fără efect contabil propriu)

---

## 1. Scop business

Furnizorii trimit avizul de livrare în Excel, cu loturi sau numere de serie, iar inventarul se numără
adesea pe foi de calcul. În Odoo standard, liniile unei recepții și cantitățile numărate se introduc una
câte una, iar greșelile de cod sau de lot se văd abia la validare.

Modulul adaugă două butoane, care deschid asistentul de import din `deltatech_import_lines`:

| Document | Buton | Ce face |
|---|---|---|
| Recepție, livrare, transfer intern (nefinalizat) | **Import linii** | fiecare rând devine o linie de transfer, cu lotul din fișier |
| Inventariere fizică | **Import cantități numărate** | completează cantitatea numărată (**Faptic**) pe produs și lot, în locația aleasă |

Operatorul vede în previzualizare rândurile cu probleme (produs negăsit, lot inexistent, număr de serie
repetat) și abia apoi importă. Importul doar pregătește documentul: recepția se validează, iar
numărătoarea se aplică de gestionar, ca în fluxul standard.

## 2. Bază legală și context

Modul operațional, fără temei fiscal propriu. Recepția, livrarea și ajustarea de inventar se validează în
fluxul standard, cu notele contabile standard.

Pentru inventar, modulul completează doar **cantitatea numărată**. Diferențele se înregistrează abia când
gestionarul apasă **Aplică** în **Inventariere fizică**, ca la o numărătoare introdusă manual.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| **Gestionar** | importă avizul furnizorului în recepție, cu loturi, și numărătoarea în inventarul fizic |
| **Operator de depozit** | importă liniile unui transfer intern sau ale unei livrări |

Drepturi: **Import linii** apare oricui poate modifica transferul. **Import cantități numărate** apare doar
utilizatorilor de stoc și în inventarul fizic (nu în raportul de stoc). Mapările salvate sunt comune
utilizatorilor companiei.

Roluri recomandate la testare: un gestionar cu loturi activate (**Inventar → Configurare → Setări → Loturi
și numere de serie**).

## 4. Conturi și date implicate

Modulul nu creează note contabile. Datele folosite:

- **produsele**, găsite după **Referință internă**, **Cod de bare** sau **Nume produs**; pe transferuri
  doar produsele de tip bun, în inventar doar produsele cu stoc urmărit (stocabile);
- **loturile**, după nume, pentru produsele urmărite pe lot sau număr de serie;
- **unitățile de măsură**, după nume (înrudite cu unitatea produsului);
- **locația inventariată**, doar locații interne;
- **mapările de coloane** (**Mapări import linii**), pe tip de document.

Date minime pentru demo:
- o recepție în ciornă, un produs urmărit pe lot (cu un lot existent) și unul fără urmărire;
- un fișier Excel cu coloanele Cod, Cantitate și Lot.

## 5. Configurare inițială

1. **Instalați** `deltatech_import_lines`; `deltatech_import_lines_stock` se instalează singur odată cu
   Inventarul.
2. Activați **Loturi și numere de serie** în setările Inventarului.
3. Pe tipul de operațiune al recepțiilor, **Creare loturi/numere de serie noi** trebuie să fie bifat
   (implicit este); altfel un lot nou nu e acceptat nici la import.
4. Opțional, pregătiți mapări din **Inventar → Configurare → Mapări import linii**; de obicei maparea se
   salvează direct din asistent.

## 6. Flux de utilizare

Scenariul: avizul furnizorului vine în `receptie.xlsx`, cu produse pe lot, apoi gestionarul importă
numărătoarea de inventar din `inventar.xlsx`. Pașii asistentului (fișier, coloane, previzualizare) sunt cei
din fișa modulului `deltatech_import_lines`; aici sunt ecranele specifice stocului. Capturile sunt generate de
testul modulului `deltatech_import_lines` și se află în `deltatech_import_lines/static/description/`.

### Pasul 1 — Recepție: coloana Lot/Număr de serie

**Inventar → Operațiuni → Recepții** → recepția în ciornă sau confirmată → butonul **Import linii** din
antet (dispare după finalizare sau anulare). În pasul de coloane, mapați o coloană pe **Lot/Număr de serie**.

- **Găsiți pe ecran:** coloanele **Produs**, **Lot/Număr de serie**, **Stare** și **Mesaj** din previzualizare.
- **Verificați:**
  - lotul existent și lotul nou sunt **OK**: pe recepții, lotul nou se creează la validare;
  - un rând cu **Eroare lot/serie** (captura arată doar rânduri **OK**) are motivul în **Mesaj**: produs fără
    urmărire, număr de serie cu cantitate diferită de 1 sau număr de serie repetat pe mai multe rânduri;
  - pe livrări și transferuri interne, lotul trebuie să existe deja.
- Apăsați **Importă** (sau bifați mai întâi **Omite rândurile cu erori**).

![Previzualizarea pe recepție, cu loturile](../../deltatech_import_lines/static/description/08_receptie_loturi.png)

### Pasul 2 — Recepția cu liniile importate

Recepția are câte o linie pe produs. Rândurile aceluiași produs cu loturi diferite apar într-o singură linie,
cu câte o operațiune detaliată pe lot. Mișcările adăugate într-un transfer confirmat se confirmă imediat, iar
Odoo le unește cu liniile existente ale aceluiași produs. Validarea rămâne pasul standard (**Validează**).

![Recepția, cu liniile importate](../../deltatech_import_lines/static/description/09_receptie_linii_importate.png)

### Pasul 3 — Inventar: butonul „Import cantități numărate"

**Inventar → Operațiuni → Inventariere fizică** → butonul **Import cantități numărate** din antetul listei.

![Inventarul fizic, cu butonul de import](../../deltatech_import_lines/static/description/10_inventar_buton_import.png)

### Pasul 4 — Locația numărată și previzualizarea

În asistent alegeți **Locație inventariată** (implicit stocul primului depozit al companiei), apoi fișierul și
coloanele, la pasul **Fișier**. Importul a cărui locație lipsește este refuzat. Locația nu se mai vede la
previzualizare, ci doar în pasul **Fișier**.

- **Găsiți pe ecran:** în previzualizare, coloanele **Produs**, **Lot/Număr de serie**, **Stare** și **Mesaj** din previzualizare.
- **Verificați:**
  - un produs urmărit pe lot sau serie are lotul completat și existent (altfel **Eroare lot/serie**:
    lotul sau numărul de serie este obligatoriu);
  - un număr de serie are cantitatea cel mult 1 și nu se repetă;
  - cantitatea 0 e acceptată, pentru produsele numărate și găsite lipsă;
  - rândurile aceluiași produs și lot se adună.

![Asistentul de inventar, previzualizarea](../../deltatech_import_lines/static/description/11_inventar_previzualizare.png)

### Pasul 5 — Cantitățile numărate în inventarul fizic

După import, lista **Inventariere fizică** arată cantitățile din fișier în coloana **Faptic**, lângă
**În stoc** și **Diferență**.

- **Găsiți pe ecran:** coloanele **În stoc**, **Faptic** și **Diferență** pe fiecare produs (și lot) din
  locația inventariată.
- **Verificați:**
  - cantitatea numărată e cea din fișier (sumată, dacă produsul apare de mai multe ori);
  - cantitatea e exprimată în unitatea produsului, chiar dacă fișierul avea altă unitate înrudită;
  - diferențele mari sunt explicate înainte de aplicare.
- Abia apoi apăsați **Aplică tot** (sau **Aplică** pe rând).

![Inventarul fizic, cu cantitățile numărate importate](../../deltatech_import_lines/static/description/12_inventar_cantitati_numarate.png)

### Note de monografie și raportare

Modulul **nu** generează note contabile. Documentele completate urmează fluxul standard:

| Operațiune (după validare) | Debit | Credit |
|---|---|---|
| Recepție mărfuri / materii prime (stoc perpetuu) | 371 Mărfuri / 301 Materii prime | 408 Furnizori - facturi nesosite |
| Factura furnizorului pentru recepție | 408 Furnizori - facturi nesosite; 4426 TVA deductibilă | 401 Furnizori |
| Livrare către client | 607 Cheltuieli privind mărfurile | 371 Mărfuri |

Plusurile și minusurile de inventar se înregistrează la **Aplică**, pe conturile configurate pentru locația
de ajustare a inventarului, ca la o numărătoare introdusă manual.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `deltatech_import_lines` | asistentul, citirea fișierului, maparea coloanelor și previzualizarea |
| `stock` (standard) | transferurile, mișcările, loturile, inventarul fizic și aplicarea lui |

**Ce e automat:**
- găsirea produselor, verificarea cantităților, unităților și loturilor înainte de import;
- crearea loturilor noi la validarea recepției, când tipul de operațiune permite;
- confirmarea mișcărilor adăugate într-un transfer confirmat;
- adunarea rândurilor aceluiași produs și lot în inventar.

**Ce rămâne manual:**
- crearea produselor și a loturilor lipsă (în afara recepțiilor);
- validarea recepției sau a livrării;
- verificarea diferențelor și aplicarea inventarului.

## 8. Verificări pentru consultant

- [ ] Butonul **Import linii** apare pe transferurile nefinalizate și dispare după finalizare sau anulare.
- [ ] Pe recepție, un lot nou e acceptat, iar pe livrare același lot e marcat **Eroare lot/serie**.
- [ ] Un lot indicat pentru un produs fără urmărire e marcat **Eroare lot/serie**.
- [ ] Un număr de serie cu cantitatea 2, sau repetat pe două rânduri, e marcat **Eroare lot/serie**.
- [ ] Cele două rânduri ale aceluiași produs, cu loturi diferite, ajung într-o singură linie de recepție, cu două operațiuni detaliate.
- [ ] **Import cantități numărate** apare în **Inventariere fizică**, pentru utilizatorii de stoc.
- [ ] Un produs urmărit pe lot, fără lot în fișier, e refuzat în inventar.
- [ ] Rândurile aceluiași produs și lot dintr-o numărătoare se adună în coloana **Faptic**, fără aplicarea inventarului.
- [ ] Un produs care nu e stocabil nu e găsit în importul de inventar (**Produs negăsit**).

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Nu se pot importa linii într-un transfer finalizat sau anulat. | transferul e închis | creați un transfer nou |
| Lotul … nu există, iar această operațiune nu poate crea loturi. | lot nou pe o livrare sau pe un transfer intern, sau tip de operațiune fără creare de loturi | creați lotul, corectați numele sau bifați **Creare loturi/numere de serie noi** pe recepții |
| Lotul … nu există. | lot necunoscut în inventar | creați lotul sau corectați numele |
| … este urmărit pe lot: lotul sau numărul de serie este obligatoriu. | produs urmărit, fără lot pe rând, în inventar | completați coloana de lot |
| … nu este urmărit pe lot sau număr de serie. | s-a indicat un lot pentru un produs fără urmărire | goliți lotul de pe rând |
| Cantitatea pentru numărul de serie … trebuie să fie 1. / … nu poate fi mai mare de 1. | număr de serie cu altă cantitate (în transfer, respectiv în inventar) | corectați cantitatea |
| Numărul de serie … apare pe mai multe rânduri. | același număr de serie repetat | păstrați un singur rând |
| Numărul de serie … al produsului … este numărat de mai multe ori. | numărul de serie ajunge la cantitate peste 1 după adunarea rândurilor, inclusiv după conversia unităților | corectați fișierul |
| Selectați locația inventarierii. | importul de inventar nu are locație | alegeți **Locație inventariată** |
| Doar utilizatorii de stoc pot importa cantități numărate. | utilizatorul nu are rol de stoc | acordați rolul de utilizator de stoc |

## 10. Capturi de ecran

Modulul nu are capturi proprii: ecranele lui sunt capturate de testul modulului de bază, în
`deltatech_import_lines/static/description/`, **generate automat** din `deltatech_import_lines/tests/test_screenshots.py`
(mixinul `ScreenshotCase` din `deltatech_doc_screenshots`, import defensiv), în română, pe compania „Demo
Import SRL" în RON:

1. `08_receptie_loturi.png` — previzualizarea pe recepție, cu loturile;
2. `09_receptie_linii_importate.png` — recepția, cu liniile importate;
3. `10_inventar_buton_import.png` — lista **Inventariere fizică**, cu butonul **Import cantități numărate**;
4. `11_inventar_previzualizare.png` — asistentul de inventar, la previzualizare (locația se alege în pasul **Fișier**, nu se vede aici);
5. `12_inventar_cantitati_numarate.png` — lista **Inventariere fizică**, cu cantitățile numărate.

Regenerare:

```bash
./odoo/odoo-bin -c odoo.conf -d <db> \
    -i deltatech_import_lines_sale,deltatech_import_lines_purchase,deltatech_import_lines_stock,deltatech_import_lines_mrp,deltatech_doc_screenshots \
    --test-tags=fise_screenshots --stop-after-init --http-port=8987 --gevent-port=8988
```

## 11. Observații pentru manual

- Prezentați importul ca pe un flux în trei pași: fișier → coloane → previzualizare. Nimic nu se scrie în
  document înainte de **Importă**.
- Explicați diferența dintre recepții (lotul nou se creează la validare) și celelalte transferuri (lotul
  trebuie să existe).
- La inventar, importul nu aplică numărătoarea: gestionarul verifică diferențele și apasă **Aplică tot**.
- Produsele urmărite pe lot sau serie se numără pe lot: fără lot, rândul nu se poate importa.
