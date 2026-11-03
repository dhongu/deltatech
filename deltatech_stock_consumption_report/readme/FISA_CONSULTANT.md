# Fișă Modul: Raportul lunar al bonurilor de consum

**Modul:** `deltatech_stock_consumption_report`
**Utilizator principal:** Contabil (închiderea de lună), gestionar / administrator stoc
**Prioritate:** 🟡 Medie (contabilitatea nu vedea consumurile din magazine; nu blochează operarea)

---

## 1. Scop business

Bonurile de consum se operează în **Inventar**, de regulă separat pe fiecare magazin sau depozit, dar
contabilitatea nu are o vedere de ansamblu asupra lor la sfârșit de lună. Modulul adaugă un **raport al consumurilor dintr-o perioadă** (implicit luna
curentă), cu **cantitate și valoare de stoc**, grupat pe **magazin** și pe **destinația consumului**
(investiții, consum propriu…), aleasă de gestionar pe fiecare bon dintr-o listă întreținută de client.
Raportul are două variante:

- **centralizat pe magazin și destinație** — câte produse s-au dat pe consum, ce cantitate și ce
  valoare;
- **detaliat pe produs** în cadrul magazinului și al destinației — cu categorie, cost mediu, marcajul „se poate vinde"
  și cantitatea livrată clienților în ultimele 6 luni, ca să se vadă dacă pe consum a ieșit **marfă
  care de fapt se vinde**, nu doar consumabile.

Raportul se vede pe ecran (pivot) și se descarcă în **Excel (XLSX)**.

## 2. Bază legală și context

Modulul **nu generează documente și nu înregistrează nimic în contabilitate** — citește mișcările
de stoc deja validate și adaugă pe bon câmpul *Destinație consum*. Contextul:

- **Bonul de consum** (formular 14-3-4A, tipărit de `l10n_ro_picking_report`) este documentul
  justificativ al ieșirii din gestiune; nota contabilă a consumului o face `l10n_ro_stock_account`
  la validarea transferului.
- **Bon de consum** înseamnă, pentru raport, un transfer validat către o locație de consum. Pe
  localizarea română sunt locațiile de tip **Consum** și **Utilizare** (dare în folosință)
  (din `l10n_ro_stock`, instalat de `l10n_ro_stock_account`); fără ea, lista de tipuri se extinde dintr-un modul de legătură.
- **Valoarea** din raport este **creditul liniilor produsului din nota contabilă a bonului**
  (ieșirea din contul de stoc, oricare ar fi contul de stoc al locației sau al depozitului), adică exact suma care a ieșit din gestiune în contabilitate — nu ultimul preț de
  achiziție și nici prețul de vânzare. Dacă bonul nu are notă contabilă (de exemplu produs cu
  valorizare periodică), raportul ia **valoarea de stoc a mișcării**.
- **Perimetrul:** raportul ia mișcările validate spre locațiile de tip **Consum** și, în plus, spre
  locațiile de tip **Utilizare** (dare în folosință) (obiecte de inventar date în folosință). Retururile din
  consum (de la locația de consum înapoi în stoc) **nu** intră.
- **Destinația consumului** este informativă: grupează raportul, dar **nu schimbă nota contabilă**
  a bonului. Conturile rămân cele din categoria produsului (secțiunea 4), indiferent dacă destinația
  e *Investiții* sau *Consum propriu*.
- Verificarea „nu s-a dat marfă de vânzare pe consum" este o verificare de **control intern**, nu o
  obligație legală; raportul doar scoate în evidență cazurile, decizia rămâne la contabil.

## 3. Utilizatori și roluri

| Rol | Ce face |
|-----|---------|
| **Contabil** | Rulează raportul la închiderea lunii, compară totalul cu rulajul conturilor de stoc din notele bonurilor de consum (nu din tot jurnalul de stoc) și verifică lista detaliată. |
| **Gestionar / responsabil magazin** | Operează bonurile de consum (Inventar → transfer de tip Consum) ca până acum și alege, pe fiecare bon, *Destinație consum*. |
| **Administrator stoc** | Întreține lista destinațiilor și are acces la raport (vezi mai jos). |

**Drept de acces:** wizard-ul este permis doar grupului **Inventar / Administrator**
(`stock.group_stock_manager`). Un contabil fără acest grup **nu vede meniul**. La testare folosiți
un utilizator cu Inventar → Administrator. Utilizatorul de Inventar vede destinațiile **doar în
lista de alegere de pe bon**; meniul *Destinații consum* și modificarea listei sunt doar pentru
administratori.

## 4. Conturi și date implicate

Raportul nu are conturi proprii; consumurile pe care le citește au fost contate de
`l10n_ro_stock_account` astfel:

| Operațiune | Debit | Credit |
|-----------|-------|--------|
| Consum materiale consumabile | 6028 Cheltuieli privind alte materiale consumabile | 3028 Alte materiale consumabile |
| Consum propriu de mărfuri | 6xx — contul de consum setat pe contul de cheltuieli al mărfii (ex. 6028) | 371 Mărfuri |
| Dare în folosință obiecte de inventar | 603 Cheltuieli privind obiectele de inventar | 303 Materiale de natura obiectelor de inventar |
| Retur din consum | **storno în roșu** pe aceleași conturi: Dr cheltuieli = Cr stoc, cu sumă negativă | |

Debitul este **contul de cheltuieli al produsului** (din categorie), înlocuit cu **Cont consum**
dacă acesta e setat pe contul de cheltuieli. **Atenție la mărfuri:** contul lor de cheltuieli este de
regulă **607**. Fără *Cont consum* setat pe 607, consumul propriu de marfă se înregistrează pe 607 și
umflă costul mărfurilor vândute. Conturile exacte se verifică în baza de date a clientului, cu contabilul.

La darea în folosință, Odoo înregistrează contul extrabilanțier 8035 **simultan pe debit și pe credit**
în aceeași notă (sold 0). Monografia corectă este **Dr 8035** la darea în folosință și **Cr 8035**
la scoaterea din uz; cum Odoo nu o face, evidența extracontabilă a obiectelor date în folosință se ține separat și se
verifică cu contabilul.

**Date minime pentru demo:**

- un depozit (magazin) cu un **tip de operațiune** al cărui *locație destinație implicită* este de tip
  **Consum** (în capturi: `NRD/CNS` — Magazin Nord și `SUD/CNS` — Magazin Sud);
- 2–3 produse stocabile, cu stoc și cost;
- două **destinații de consum** (ex. *Consum propriu* și *Investiții*);
- cel puțin două bonuri de consum **validate** în luna raportată, pe destinații diferite.

## 5. Configurare inițială

1. Instalați modulul (depinde de `stock_account`). Pentru tipurile de locație *Consum* și *Dare în
   folosință* trebuie instalat și `l10n_ro_stock_account`.
2. Dați utilizatorului care rulează raportul grupul **Inventar → Administrator**.
3. Verificați că fiecare magazin are un tip de operațiune pentru consum, cu destinația implicită o
   locație de tip **Consum** (Inventar → Configurare → Tipuri de operațiuni). Raportul preselectează
   automat toate tipurile de operațiune ale companiei care au o astfel de destinație (sau una de tip *Utilizare* (dare în folosință)).
4. Pe contul de cheltuieli al categoriilor de **mărfuri** (607) setați **Cont consum** (ex. 6028)
   — Contabilitate → Configurare → Plan de conturi → contul 607 → câmpul *Cont consum*. Altfel,
   consumul propriu de marfă ajunge pe 607 (vezi secțiunea 4).
5. Definiți **destinațiile consumului** — **Inventar → Configurare → Destinații consum** (pasul 1 din
   fluxul de mai jos). Lista e **goală la instalare** și trebuie completată înainte de primul bon
   nou, altfel bonul nu se poate salva.
6. Verificați denumirea depozitelor (Inventar → Configurare → Depozite): în raport, **magazinul** apare
   cu numele depozitului tipului de operațiune.

## 6. Flux de utilizare

### Pasul 1 — Lista destinațiilor consumului

**Inventar → Configurare → Destinații consum.** Administratorul stocului adaugă destinațiile pe care
le folosesc magazinele (ex. *Consum propriu*, *Investiții*), direct în listă, cu **Nou**. Ordinea se
schimbă trăgând de mânerul din stânga; o destinație care nu mai e folosită se **arhivează**, nu se
șterge, ca bonurile vechi să o păstreze.

![Lista destinațiilor consumului, cu coloanele Nume și Companie: Consum propriu și Investiții, ambele pe RO Company](../static/description/01_destinatii_consum.png)

### Pasul 2 — Bonul de consum, cu destinația

Gestionarul operează consumul ca până acum: **Inventar → Imagine de ansamblu → cardul
*Magazin Nord: Consum*** (sau *Magazin Sud: Consum*) → **Nou**, produsele și cantitățile, apoi **Validează**.
Nou este câmpul **Destinație consum**, în dreapta, sub *Document sursă*:

- apare **doar pe bonurile de consum** (destinația transferului e o locație de consum: pe localizarea
  română, de tip *Consum* sau *Utilizare* (dare în folosință));
- este **obligatoriu** pe orice bon de consum nevalidat (inclusiv pe cele vechi aflate în ciornă sau
  gata) — fără el bonul nu se poate salva;
- se poate completa și pe bonurile **deja validate**, ca să fie încadrate consumurile de dinainte de
  instalarea câmpului;
- la **Retur**, bonul de retur preia destinația bonului inițial. Pe formularul returului câmpul nu
  se vede (returul intră în stoc, nu în consum); destinația lui se vede în **Inventar → Operații →
  Transferuri**, grupat după *Destinație consum* (gruparea e în meniul de căutare).

La validare, mișcarea primește **valoarea de stoc** cu care a ieșit produsul și se face nota contabilă. Raportul ia în calcul
**doar bonurile validate** (starea *Efectuat*).

![Bonul de consum NRD/CNS/00001 în starea Efectuat: Tip operație Magazin Nord: Consum, Destinație consum Consum propriu, cu mănuși, detergent și ciment pe liniile de operații](../static/description/02_bon_consum.png)

### Pasul 3 — Nota contabilă a bonului

La validare, `l10n_ro_stock_account` înregistrează nota de consum în jurnalul de stoc: debit contul
de consum, credit contul de stoc al produsului, cu **aceeași valoare** care apare apoi în raport.
Nota se deschide din bon (butonul **Elemente jurnal** din partea de sus) sau din **Contabilitate (sau
Facturare) → Contabilitate → Elemente jurnal**, căutând după referința bonului (ex. `NRD/CNS/00001`).
Destinația consumului nu schimbă conturile notei.

În exemplu, bonul `NRD/CNS/00001` are o notă de 107,56 lei: mănușile și detergentul (materiale
consumabile) merg Dr 6028 = Cr 3028, iar cimentul (marfă) Dr 6028 = Cr 371, prin *Cont consum*
setat pe 607. Raportul ia valoarea din această notă (creditul pe 3028 și 371), deci aceeași sumă, 107,56, apare pe
rândul *Consum propriu* al magazinului *Magazin Nord* din pivotul de la Pasul 5.

![Nota contabilă a bonului NRD/CNS/00001, tabul Elemente jurnal: Dr 6028 pe cele trei produse, Cr 3028 pentru consumabile și Cr 371 pentru ciment, total 107,56 lei](../static/description/03_nota_consum.png)

### Pasul 4 — Deschiderea raportului

**Inventar → Raportare → Raport consumuri.** Se deschide fereastra raportului, cu:

- **Companie** — apare doar dacă lucrați în mai multe companii;
- **De la data** / **Până la data** — implicit prima și ultima zi a lunii curente; pentru închiderea
  lunii trecute, schimbați ambele date;
- **Tipuri de operațiune** — implicit toate tipurile ale căror destinație implicită este o locație
  de consum sau de dare în folosință (în capturi: Magazin Nord și Magazin Sud). Puteți păstra doar unul, ca
  să rulați raportul pe un singur magazin. Dacă goliți câmpul, intră **toate** mișcările spre locații
  de consum / dare în folosință din perioadă, indiferent de tipul de operațiune.

![Fereastra Raport consumuri: De la data 1 nov., Până la data 30 nov., Tipuri de operațiune Magazin Nord: Consum și Magazin Sud: Consum, butoanele Export XLSX și Vizualizare](../static/description/04_wizard_raport.png)

### Pasul 5 — Verificarea pe ecran (pivot)

Apăsați **Vizualizare**. Se deschide un **pivot** pe mișcările de consum din perioadă:

1. **Găsiți pe ecran** — pe rânduri, fiecare **magazin** (depozitul tipului de operațiune), desfăcut pe
   **destinație** și apoi pe **produse**; pe coloane, **Cantitate** și **Valoare**. Rândul *Total* de
   sus este suma tuturor magazinelor. Totalul de *Cantitate* adună unități de măsură diferite și e
   orientativ; se reconciliază doar *Valoare*. Pivotul și Excel-ul au aceleași cifre (sunt calculate
   o singură dată, la apăsarea butonului).
2. **Verificați:**
   - apar **toate magazinele** care au avut consumuri în lună (dacă lipsește unul, verificați
     tipurile de operațiune selectate la Pasul 4);
   - **nu există rânduri *Nedefinit*** — ele sunt bonuri fără destinație; completați destinația pe
     bonurile respective (Pasul 2) și rulați din nou raportul;
   - **nicio valoare nu este 0** pe un produs cu cantitate — o valoare 0 înseamnă o mișcare fără
     cost (produs fără cost la momentul ieșirii) și trebuie lămurită înainte de închidere;
   - **totalul valorii** (minus retururile din consum ale lunii) este egal cu rulajul creditor net al
     conturilor de stoc din **notele bonurilor de consum** ale lunii — **Contabilitate (sau Facturare) →
     Contabilitate → Elemente jurnal**, filtrat pe perioadă și pe *Etichetă* care conține prefixul tipului de
     consum (ex. `/CNS/`), grupat pe cont. Dacă tipul de consum are configurat un tip de retur separat, includeți în filtru
     și prefixul acestuia. Nu luați tot jurnalul de stoc: el conține și livrările
     (Dr 607 = Cr 371), deci rulajul lui 371 ar include costul mărfurilor vândute. Retururile din
     consum sunt storno în roșu, deci micșorează rulajul creditor.
3. **Treceți mai departe** — dacă cifrele sunt confirmate, închideți pivotul și reveniți la
   fereastra raportului pentru export. Din pivot se poate descărca și direct un Excel standard Odoo
   (butonul de descărcare din pivot), dar exportul de mai jos are formatul pentru contabilitate.

În exemplu, Magazin Nord are 233,96 lei, din care *Consum propriu* 107,56 și *Investiții* 126,40 (10
saci de ciment), iar Magazin Sud 24,65 lei, tot *Consum propriu*; total 258,61 lei.

![Pivotul Consumuri: Magazin Nord desfăcut pe Consum propriu 107,56 lei și Investiții 126,40 lei, Magazin Sud cu Consum propriu 24,65 lei, apoi pe produse; total 258,61 lei](../static/description/05_pivot_consumuri.png)

### Pasul 6 — Exportul XLSX: foaia centralizată

Din fereastra raportului apăsați **Export XLSX**. Fișierul (`consumuri_<de la>_<până la>.xlsx`)
apare în fereastră, gata de descărcat. Prima foaie, **Centralizat**, are câte un rând pe **magazin ×
destinație**:

1. **Găsiți** — coloanele *Magazin*, *Destinație*, *Produse* (câte produse distincte pe rând; pe
   rândul *Total* se adună contoarele rândurilor, deci un produs consumat în ambele magazine sau pe
   două destinații e numărat de mai multe ori), *Cantitate*, *Valoare* și *Produse vândute în
   ultimele 6 luni* (câte dintre produse s-au și vândut clienților); ultimul rând este **Total**.
2. **Verificați** — totalul din *Valoare* este **același** cu totalul din pivotul de la Pasul 5 și cu
   contabilitatea; perioada din antet (*Perioada*) este luna corectă; nu există rânduri cu destinația
   *Nedefinit*.
3. **Treceți mai departe** la foaia de detaliu dacă *Produse vândute în ultimele 6 luni* nu este 0.

Capturile sunt pe date demonstrative.

![Foaia Centralizat a exportului XLSX: rândurile Magazin Nord Consum propriu 107,56, Magazin Nord Investiții 126,40 și Magazin Sud Consum propriu 24,65, cu Total 258,61](../static/description/06_xlsx_centralizat.png)

### Pasul 7 — Exportul XLSX: foaia detaliată pe produs

A doua foaie, **Detaliat**, are câte un rând pe **magazin × destinație × produs**:

1. **Găsiți** — *Magazin*, *Destinație*, *Cod*, *Produs*, *Categorie*, *UM*, *Cantitate*, *Valoare*,
   *Cost mediu* (valoare / cantitate), *Se poate vinde* (bifa produsului) și *Livrat clienților
   (ultimele 6 luni)* — cantitatea livrată clienților **pe toată compania** (nu doar din magazinul
   rândului), începând cu 6 luni înainte de sfârșitul perioadei, **brută** (retururile de la clienți
   nu se scad). Rulat retroactiv, raportul include și livrările de după perioadă.
2. **Verificați** — produsele cu **cantitate mare livrată clienților** sunt marfă care se vinde
   efectiv; dacă au ieșit pe consum în cantități mari, verificați destinația și cereți justificarea
   magazinului. Când categoriile nu separă consumabilele de marfă (de exemplu sunt pe furnizor) și
   aproape toate produsele au bifa „Se poate vinde", **coloana relevantă este cea cu livrările către
   clienți**, nu categoria.
3. **Treceți mai departe** — fișierul se transmite contabilității / se arhivează cu închiderea lunii.

![Foaia Detaliat a exportului XLSX: câte un rând pe magazin, destinație și produs; cimentul apare la Magazin Nord pe Consum propriu (4) și pe Investiții (10), cu 30 livrate clienților](../static/description/07_xlsx_detaliat.png)

### Note de monografie și raportare

Raportul **nu creează note contabile**. Notele pe care le reflectă sunt cele ale bonurilor de consum:

```
Consum materiale consumabile:   Dr 6028 = Cr 3028
Consum propriu de mărfuri:      Dr 6028 (Cont consum al lui 607) = Cr 371
Dare în folosință:              Dr 603  = Cr 303
                                extracontabil corect: Dr 8035 (la scoaterea din uz Cr 8035);
                                Odoo pune 8035 pe ambele laturi, evidența se ține separat
Retur din consum:               storno în roșu al notei de consum (sume negative)
```

Retururile din consum **nu** intră în raport: el ia doar mișcările cu destinația locație de consum /
dare în folosință. Dacă în lună au existat retururi, totalul raportului este mai mare decât rulajul
net al notelor de consum.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|-------|-----|
| `stock_account` / `l10n_ro_stock_account` (pe localizarea RO) | Face nota contabilă a bonului; raportul ia valoarea din ea (creditul liniilor produsului). |
| `l10n_ro_stock_account` (opțional) | Aduce tipurile de locație *Consum* / *Utilizare* (dare în folosință) și notele de consum pe conturile RO. |
| `l10n_ro_picking_report` (dacă este instalat) | Tipărește bonul de consum (14-3-4A) pe fiecare transfer; raportul este varianta cumulată pe lună. |
| `stock` | Transferurile, tipurile de operațiune, locațiile de consum și depozitele (magazinele); câmpul *Destinație consum* stă pe transfer. |

**Ce e automat:** preselecția tipurilor de operațiune de consum, perioada implicită (luna curentă),
gruparea pe magazin și destinație, preluarea destinației pe bonul de retur, calculul costului mediu și al livrărilor către clienți din ultimele 6 luni.

**Ce rămâne manual:** întreținerea listei de destinații, alegerea destinației pe fiecare bon (și
completarea ei pe bonurile vechi), alegerea perioadei la închiderea lunii trecute, reconcilierea totalului cu
contabilitatea și decizia asupra produselor de vânzare ieșite pe consum.

## 8. Verificări pentru consultant

- [ ] **Inventar → Configurare → Destinații consum** permite adăugarea unei destinații unui
      administrator; un utilizator de Inventar fără drept de administrator nu vede meniul, dar poate
      alege destinația pe bon.
- [ ] Pe un bon de consum nou, *Destinație consum* este obligatorie (bonul nu se salvează fără ea);
      pe o recepție sau o livrare câmpul nu apare.
- [ ] Returul unui bon de consum are aceeași destinație ca bonul inițial (Inventar → Operații →
      Transferuri, grupat după *Destinație consum*).
- [ ] Meniul **Inventar → Raportare → Raport consumuri** apare pentru un utilizator cu Inventar →
      Administrator și **nu** apare pentru unul fără acest grup.
- [ ] La deschidere, perioada este luna curentă și tipurile de operațiune de consum ale companiei
      sunt preselectate.
- [ ] Pivotul (**Vizualizare**) arată fiecare magazin desfăcut pe destinații și produse; totalul
      valorii pe magazin și destinație este egal cu suma bonurilor de consum validate în perioadă cu
      acea destinație.
- [ ] Un bon fără destinație apare pe rândul *Nedefinit*; după completarea destinației trece pe
      rândul destinației.
- [ ] Un bon de consum **nevalidat** (ciornă / gata) nu apare în raport.
- [ ] Un bon validat în prima zi a lunii, după miezul nopții ora României, intră în luna respectivă
      (perioada se aplică pe fusul orar al utilizatorului).
- [ ] **Export XLSX** produce fișierul cu foile *Centralizat* și *Detaliat*, ambele cu coloana
      *Destinație*; totalul din *Centralizat* = totalul din pivot = suma *Valoare* din *Detaliat*.
- [ ] Coloana *Livrat clienților (ultimele 6 luni)* este completată pentru un produs care s-a
      vândut în ultimele 6 luni și 0 pentru unul care nu s-a vândut.
- [ ] Nota contabilă a unui bon de consum are aceeași valoare ca rândul bonului în pivot.
- [ ] Totalul valorii din raport, minus retururile din consum ale lunii, = rulajul creditor net
      (cu storno) al conturilor de stoc din notele bonurilor de consum / dare în folosință ale lunii
      (filtrate după prefixul tipului de operațiune, ex. `/CNS/` — nu tot jurnalul de stoc).
- [ ] Consumul de marfă se înregistrează pe contul de consum (ex. 6028), nu pe 607.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| Bonul de consum nu se salvează: câmpul *Destinație consum* e marcat cu roșu | Destinația este obligatorie pe bonurile de consum noi | Alegeți destinația; dacă lista e goală, administratorul o completează în Inventar → Configurare → Destinații consum |
| Destinația dorită nu apare în listă pe bon | Destinația este arhivată sau e pe altă companie | Dezarhivați-o / corectați compania în Inventar → Configurare → Destinații consum |
| Rânduri *Nedefinit* în raport | Bonuri validate fără destinație: cele de dinainte de instalarea câmpului sau cele create prin import, API ori Barcode, unde câmpul nu e obligatoriu | Completați *Destinație consum* pe bonurile respective și rulați din nou raportul |
| Meniul *Raport consumuri* nu apare | Utilizatorul nu are grupul Inventar → Administrator | Adăugați grupul în Setări → Utilizatori |
| Lipsește un magazin din raport | Tipul lui de operațiune nu are destinația implicită o locație de tip *Consum* sau *Utilizare* (dare în folosință), deci nu e preselectat | Corectați destinația implicită a tipului de operațiune sau adăugați-l manual în *Tipuri de operațiune* |
| Valoare 0 pe un produs cu cantitate | Bonul nu are notă contabilă (valorizare periodică) și produsul nu avea cost la momentul ieșirii | Verificați costul produsului și mișcarea; corecția valorii se face în contabilitate, nu în raport |
| Totalul nu se potrivește cu contabilitatea | În lună au existat retururi din consum (storno în roșu) sau consumuri pe alte tipuri de operațiune decât cele selectate | Goliți *Tipuri de operațiune* (toate consumurile) și scădeți retururile din consum din total |
| Consumul de marfă apare pe 607 | Contul 607 nu are *Cont consum* setat | Setați *Cont consum* (ex. 6028) pe 607 — secțiunea 5, pasul 4 |
| Eroare „Object stock.consumption.report.wizard doesn't exist" după instalare | Modulul a fost instalat din shell, iar serverul web nu și-a reîncărcat registry-ul | Reporniți serverul (pe odoo.sh: `odoosh-restart http`) |

## 10. Capturi de ecran

Capturile (`static/description/`) se **generează automat** din `tests/test_screenshots.py` (mixinul
`ScreenshotCase` din `deltatech_doc_screenshots`, import defensiv), în **limba română**, pe planul de
conturi RO, cu `l10n_ro_stock_account` instalat. Din aceleași shot-uri se generează și capturile în
engleză din `static/description/en/`, pentru `readme/USAGE.md`:

1. `01_destinatii_consum.png` — lista destinațiilor consumului (Consum propriu, Investiții).
2. `02_bon_consum.png` — bonul de consum validat, cu *Tip operație* și *Destinație consum* marcate.
3. `03_nota_consum.png` — nota contabilă a bonului: Dr cont de consum, Cr cont de stoc.
4. `04_wizard_raport.png` — fereastra raportului: perioada și tipurile de operațiune de consum.
5. `05_pivot_consumuri.png` — pivotul consumurilor, magazin × destinație × produs, cu cantitate și valoare.
6. `06_xlsx_centralizat.png` — exportul XLSX, foaia centralizată pe magazin și destinație.
7. `07_xlsx_detaliat.png` — exportul XLSX, foaia detaliată pe magazin, destinație și produs.

Regenerare:

```bash
./odoo/odoo-bin -c odoo.conf -d <db> \
    -i deltatech_stock_consumption_report,deltatech_doc_screenshots,l10n_ro_stock_account \
    --without-demo=all --test-tags=fise_screenshots --stop-after-init
```

## 11. Observații pentru manual

- Etichetele (meniuri, butoane, coloanele din Excel) sunt **în română** pentru utilizatorii cu limba
  română; un utilizator cu limba engleză vede *Consumption report*, *Consumption purposes*, foile
  *Summary* / *Detail*.
- Destinația consumului **nu schimbă nota contabilă**. Dacă clientul vrea ca investițiile să meargă
  pe alt cont decât consumul, e o cerință separată, de stabilit cu contabilul.
- Totalul pe destinația *Investiții* este baza notei de capitalizare a investiției în regie proprie
  (Dr 231 = Cr 722), care se face manual, cu contabilul: e componenta de materiale; manopera și
  celelalte costuri directe se adaugă separat.
- Destinațiile pentru scopuri fără legătură cu activitatea economică (ex. uz personal) pot cere
  colectarea TVA (livrare asimilată); se stabilesc cu contabilul, modulul nu calculează TVA.
- **Magazinul** din raport este depozitul tipului de operațiune de consum; denumirea depozitelor
  trebuie să fie cea pe care o recunoaște contabilul.
- Insistați pe ordinea **verificare pe ecran → export**: contabilul confirmă întâi totalul din pivot
  cu contabilitatea, abia apoi trimite Excel-ul.
- Capturile foilor Excel (06, 07) sunt randate ca tabel simplu: datele și formatul numerelor sunt cele
  din fișier, dar fără culorile și lățimile de coloană din Excel.
- Coloana *Livrat clienților (ultimele 6 luni)* este „semnalul" pentru marfa de vânzare dată pe
  consum, când categoria și bifa „Se poate vinde" nu ajută (aproape toate produsele sunt vandabile).
