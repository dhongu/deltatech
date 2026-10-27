# Fișă Modul: Analitic pe echipe de vânzări și împărțirea sumelor analitice

**Modul:** `deltatech_account_analytic`
**Utilizator principal:** Contabil / controller de gestiune (contabilitate analitică)
**Prioritate:** 🟡 Medie (nu modifică notele contabile, dar schimbă repartizarea analitică a veniturilor și a costurilor)

---

## 1. Scop business

Firmele care urmăresc rezultatul pe echipe de vânzări sau pe centre de cost au două nevoi pe care
contabilitatea analitică standard nu le acoperă direct:

- **Analitic automat după echipa de vânzări.** Pe facturile către clienți, distribuția analitică se
  alege după **echipa de vânzări** a facturii, dintr-un model de distribuție analitică legat de acea
  echipă. Liniile analitice create din facturi, din chitanțe de vânzare și din notele de stoc ale
  livrărilor păstrează echipa, deci rapoartele analitice se pot grupa pe **Echipa vânzări** și pe
  **Categoria produsului**.
- **Împărțirea unei sume analitice pe mai multe conturi.** O sumă (de exemplu un cost comun: chirie,
  utilități, salarii indirecte) sau o linie analitică existentă se împarte pe mai multe conturi
  analitice după procente fixe, dintr-un șablon de împărțire, cu un document care se confirmă și, la
  nevoie, se anulează.

## 2. Bază legală și context

Contabilitatea de gestiune este opțională și se organizează după nevoile firmei; OMFP 1802/2014 lasă
entității alegerea metodei de calcul al costurilor și a conturilor de gestiune. Modulul lucrează doar
în **contabilitatea analitică** din Odoo (liniile analitice): **nu** creează și nu modifică note
contabile în conturile din planul general, deci nu are efect asupra balanței, a declarațiilor ANAF sau
a SAF-T.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Contabil cu drept de contabilitate analitică | Configurează modelele de distribuție analitică pe echipe, citește rapoartele analitice grupate pe echipă și categorie |
| Utilizator cu grupul **Analitic split user** | Creează șabloane de împărțire și documente de împărțire, le calculează și le confirmă |
| Agent de vânzări | Alege echipa de vânzări pe factură; analiticul se completează singur |

Roluri recomandate pentru testare: un utilizator cu **Contabilitate analitică** activă (Facturare /
Contabilitate → Configurare → Setări → **Contabilitate analitică**) și cu grupul tehnic
**Analitic split user** bifat pe fișa utilizatorului (Setări → Utilizatori → utilizatorul → drepturile
tehnice). Fără acest grup, meniurile de împărțire dau eroare de acces.

## 4. Conturi și date implicate

Nu sunt implicate conturi din planul de conturi; sunt implicate doar conturi **analitice**.

Date minime pentru demo:

- contabilitatea analitică activă și un plan analitic cu cel puțin trei conturi analitice (de exemplu
  „Echipa Nord”, „Echipa Sud”, „Cheltuieli comune”);
- două echipe de vânzări (**Vânzări → Configurare → Echipe de vânzări**);
- un produs vândut, cu o categorie de produs;
- o factură de furnizor sau o linie analitică cu o sumă de împărțit (de exemplu chiria lunară, 1.000 lei).

## 5. Configurare inițială

1. Activați **Contabilitate analitică** în setările Facturare / Contabilitate.
2. Bifați grupul **Analitic split user** pe utilizatorii care fac împărțiri.
3. Pentru fiecare echipă de vânzări, creați un model de distribuție analitică: **Contabilitate →
   Configurare → Contabilitate analitică → Analytic Distribution Models** → **Nou**. În formular,
   completați câmpul **Sale team** (*Echipa vânzări*), adăugat de modul, și distribuția analitică
   (de exemplu 100% pe contul „Echipa Nord”). Pentru o echipă trebuie să existe **un singur** model;
   dacă sunt mai multe, modulul nu alege niciunul.
4. Creați șabloanele de împărțire: **Contabilitate → Configurare → Contabilitate analitică →
   Analytic split templates** → **Nou**. Dați un nume, apoi în tabul **Lines templates** adăugați
   rândurile cu contul analitic și **Percent %**. Totalul procentelor trebuie să fie exact 100.

## 6. Flux de utilizare

> Fișă text: pașii nu au capturi de ecran.

### Pasul 1 — Factura către client primește analiticul echipei

**Facturare → Clienți → Facturi** → **Nou**. Alegeți clientul, apoi în tabul **Alte informații**
alegeți **Echipa de vânzări**. Adăugați o linie de produs.

Ce se întâmplă: pe fiecare linie de produs, distribuția analitică este luată din modelul de
distribuție legat de echipa facturii. Dacă schimbați echipa pe o factură existentă (încă în ciornă),
distribuția liniilor se recalculează după noua echipă. Același lucru se aplică notelor de credit către
clienți și chitanțelor de vânzare.

Verificați pe linie coloana **Analitic**: arată contul analitic al echipei.

### Pasul 2 — Confirmarea facturii și liniile analitice cu echipă

Apăsați **Confirmă**. Odoo creează liniile analitice ale facturii; modulul copiază pe ele **echipa de
vânzări** a facturii și **categoria produsului**.

Liniile analitice create din notele de stoc ale unei livrări legate de o comandă de vânzare primesc
echipa comenzii (când modulele de stoc și vânzări cu stoc sunt instalate). Pe facturile de furnizor,
dacă un cont analitic din distribuție are **același nume** cu o echipă de vânzări, linia analitică
primește acea echipă.

### Pasul 3 — Analiza pe echipe și categorii

**Contabilitate → Contabilitate → Tranzacții → Analytic Items** (sau raportul analitic din
**Contabilitate → Raportare**).

1. **Găsiți pe ecran:** în meniul de grupare al căutării există două grupări noi, **Sale team**
   (*Echipa vânzări*) și **Product category** (*Categorie produs*). Grupați după **Sale team**: fiecare
   grup este o echipă, iar coloana **Sumă** arată totalul veniturilor și al costurilor ei.
2. **Verificați:** suma grupului echipei corespunde totalului fără TVA al facturilor confirmate ale
   echipei din perioadă; liniile fără echipă apar în grupul **Nedefinit** și provin din documente fără
   echipă (de exemplu note contabile manuale).
3. **Treceți mai departe:** exportați lista cu **Acțiuni → Export** sau treceți în vizualizarea pivot,
   după ce totalurile pe echipă sunt confirmate.

### Pasul 4 — Crearea unei împărțiri pe sumă

**Contabilitate → Configurare → Contabilitate analitică → Analytic splits** → **Nou**.

Completați **Name**, **Date**, **Split type** = **Amount**, alegeți șablonul de împărțire și
introduceți **Amount** (de exemplu 1.000).

Apăsați **Compute**. În tabul **Lines templates** apar rândurile șablonului, fiecare cu contul analitic,
procentul și suma calculată (de exemplu 60% → 600, 40% → 400). Rândurile se mai pot corecta manual
cât timp documentul e în ciornă.

### Pasul 5 — Confirmarea împărțirii

Apăsați **Confirm**. Modulul verifică întâi că există rânduri și că totalul lor este egal cu suma de
împărțit, apoi creează câte o linie analitică pentru fiecare rând, cu numele și data documentului.
Documentul trece în starea **Confirmed**.

Pentru o împărțire de tip **Amount** confirmată, butonul **Reset** șterge liniile analitice create și
readuce documentul în **Draft**, ca să fie corectat și confirmat din nou.

### Pasul 6 — Împărțirea unei linii analitice existente

Pe un document nou alegeți **Split type** = **Line**. Apare câmpul **Line to split**: alegeți linia
analitică de împărțit (de exemplu linia de chirie a facturii de furnizor). Suma se ia din linie la
**Compute**, iar câmpul **Amount** nu se mai editează.

La **Confirm**, se creează liniile analitice noi (cu numele „<nume document> | <nume linie>”), iar linia
originală se **șterge**. O împărțire de tip **Line** nu se mai poate reseta: **Reset** dă eroare,
pentru că linia originală nu mai există.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr) și nu schimbă conturile din planul general. Efectele sunt
numai în contabilitatea analitică:

- factura către client: liniile analitice ale veniturilor (de exemplu cont 707 / 704) merg pe contul
  analitic al echipei de vânzări și poartă echipa și categoria produsului;
- împărțirea: suma se mută de pe linia originală (sau din nimic, la tipul **Amount**) pe conturile
  analitice din șablon. La tipul **Amount**, liniile create se adaugă celor existente, deci suma nu
  trebuie să fie deja înregistrată analitic pe alt cont, altfel apare de două ori în analiză.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `account`, `analytic` | Liniile analitice, modelele de distribuție analitică |
| `sale` | Echipele de vânzări, echipa pe factură |
| `purchase` | Facturile de furnizor ale căror linii analitice primesc echipa după nume |
| `stock_account`, `sale_stock` (opțional) | Echipa comenzii pe liniile analitice din notele de stoc ale livrărilor |

**Ce e automat:** alegerea distribuției analitice după echipă pe facturile către clienți, echipa și
categoria produsului pe liniile analitice, calculul rândurilor din șablon, verificarea totalului la
confirmare.

**Ce rămâne manual:** crearea modelelor de distribuție pe echipe (unul pe echipă), a șabloanelor de
împărțire și a documentelor de împărțire; alegerea echipei pe factură.

Nu există legături cu declarații ANAF.

## 8. Verificări pentru consultant

- [ ] Pe o factură către client cu echipa „Echipa Nord”, linia de produs are analiticul modelului
  legat de „Echipa Nord”.
- [ ] Schimbarea echipei pe factura în ciornă schimbă analiticul liniilor.
- [ ] După confirmare, liniile analitice ale facturii au **Sale team** și **Product category**
  completate.
- [ ] În **Analytic Items**, gruparea **Sale team** dă totalul pe echipă, egal cu facturile echipei.
- [ ] Un șablon cu procente care nu însumează 100 dă eroare la **Compute**.
- [ ] **Confirm** fără **Compute** dă eroare și nu creează nimic.
- [ ] O împărțire **Amount** de 1.000 pe 60/40 creează două linii analitice, de 600 și 400.
- [ ] **Reset** pe împărțirea **Amount** șterge cele două linii și readuce documentul în **Draft**.
- [ ] O împărțire **Line** confirmată înlocuiește linia originală cu liniile din șablon, cu același
  total.
- [ ] Un al doilea **Confirm** pe un document deja confirmat dă eroare.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `You must select a split template` | Nu s-a ales șablonul înainte de **Compute** | Alegeți șablonul |
| `Invalid template. Sum of percents must be 100` | Procentele din șablon nu însumează 100 | Corectați rândurile șablonului |
| `Amount must be non-zero` | Suma de împărțit este 0 (sau linia aleasă are suma 0) | Introduceți suma sau alegeți altă linie |
| `There are no split lines. Use Compute before Confirm.` | **Confirm** apăsat înainte de **Compute** sau după ștergerea rândurilor | Apăsați **Compute** |
| `The split lines total X, but Y must be split.` | Rândurile corectate manual nu mai dau suma de împărțit | Corectați sumele sau reluați **Compute** |
| `Select the analytic line to split.` | Tip **Line** fără linie aleasă (sau linia a fost ștearsă) | Alegeți linia în **Line to split** |
| `The split ... is already confirmed.` | Documentul a fost deja confirmat | Folosiți **Reset** (doar tip **Amount**) sau creați alt document |
| `This operation is not permitted for this type of split (Line)` | **Reset** pe o împărțire de tip **Line** | Corectați cu un document nou; linia originală nu mai există |
| Eroare de acces la deschiderea meniului de împărțire | Utilizatorul nu are grupul **Analitic split user** | Bifați grupul pe utilizator |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Dacă se
vor adăuga capturi, ele se generează cu skill-ul `fisa-screenshots` și se leagă în pașii 1–6 din
secțiunea 6.

## 11. Observații pentru manual

- Regula „un singur model de distribuție pe echipă” trebuie spusă explicit: cu două modele pe aceeași
  echipă, modulul nu aplică niciunul și linia rămâne cu analiticul standard.
- Legătura facturilor de furnizor cu echipa se face după **numele** contului analitic, care trebuie să
  fie identic cu numele echipei; redactorul manualului păstrează această convenție.
- Etichetele noi ale modulului (**Analytic splits**, **Compute**, **Confirm**, **Reset**,
  **Lines templates**) apar în engleză și în interfața în română, pentru că nu au încă traducere.
- Descrierea modulului (`readme/DESCRIPTION.md`) menționează o opțiune „Split Sale Analytic” și
  câmpuri de împărțire pe contul analitic; acestea **nu** există în versiunea 20.0 (setarea este
  dezactivată în cod), deci nu se documentează în manual.
