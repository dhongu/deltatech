# Fișă Modul: Componente alternative în producție

**Modul:** `deltatech_mrp_bom_alternative`
**Utilizator principal:** Tehnolog / responsabil producție
**Prioritate:** 🟡 Medie (evită blocarea producției când lipsește o componentă; fără efect contabil propriu)

---

## 1. Scop business

O comandă de producție se blochează când lipsește o singură componentă, deși în depozit există un
înlocuitor acceptat tehnologic (altă rășină, alt furnizor al aceleiași piese). În Odoo standard,
operatorul trebuie să modifice manual componentele comenzii, fără regulă de conversie și fără urmă a
înlocuirii.

Modulul permite definirea, pe fiecare linie a listei de materiale, a **componentelor alternative**, fiecare
cu cantitatea ei echivalentă (1 kg de rășină = 1.200 g din altă rășină), prioritate și perioadă de
valabilitate. Pe comanda de producție, înlocuirea se face **manual**, cu butonul de substituire, sau
**automat**, la confirmare și la verificarea disponibilității, din alternativele aflate în stoc. Fiecare
înlocuire rămâne trasabilă: mișcarea păstrează componenta înlocuită, iar raportul **Component
Substitutions** arată ce s-a consumat în locul a ce.

## 2. Bază legală și context

Modulul nu are implicații fiscale și nu generează note contabile proprii. Contextul este tehnologic și de
control intern: înlocuirea unei componente trebuie să fie aprobată tehnologic (definită pe lista de
materiale) și documentată (mesaj pe comandă, raport de substituiri), ca abaterile de consum față de
rețetă să poată fi justificate.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Tehnolog (**Manufacturing / Administrator**) | Definește alternativele pe liniile listei de materiale, alege politica de substituire, configurează setările |
| Responsabil producție (**Manufacturing / User**) | Confirmă comenzile, verifică disponibilitatea, face substituirile manuale, consultă raportul |

Alternativele se creează și se modifică doar de **Manufacturing / Administrator**; **Manufacturing /
User** le vede și le folosește pe comenzi. Meniul **BoM Alternatives** este doar pentru administratori.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile direct. Componenta alternativă se consumă și se contabilizează ca
orice componentă (vezi „Note de monografie”).

Date minime pentru demo:

- un produs finit cu listă de materiale, cu o componentă *Rășină A* (1 kg pe bucată);
- o componentă alternativă *Rășină B*, în altă unitate (grame), cu stoc;
- stoc insuficient din *Rășină A* (de exemplu 2 kg pentru o comandă de 5 bucăți).

## 5. Configurare inițială

1. Instalați modulul `deltatech_mrp_bom_alternative` (depinde de `mrp`).
2. **Manufacturing → Configuration → Settings**, blocul **Operations**:
   - **Partial Substitution** (bifat implicit) — o componentă se poate împărți între originală și una sau
     mai multe alternative; debifat, o alternativă se folosește doar dacă acoperă singură toată lipsa;
   - **Substitute on Availability Check** (bifat implicit) — substituirea automată se reia la **Check
     Availability**, nu doar la confirmare.
   Setările sunt pe companie.
3. **Manufacturing → Products → Bills of Materials**, deschideți lista și salvați-o. Pe fiecare linie de
   componentă, coloana **Substitution** arată politica, iar butonul cu săgeți (**Alternatives**, estompat
   când linia nu are încă alternative) deschide fereastra de alternative.
4. În fereastra **Alternatives for <componentă>**:
   - alegeți **Substitution**: *Manual* (alternativele se aleg pe comandă) sau *Automatic* (lipsa se
     acoperă singură din alternative, în ordinea lor);
   - adăugați rânduri: **Alternative Component**, **Quantity** și **Unit** (cantitatea alternativei care
     înlocuiește cantitatea componentei originale afișate sus), opțional **Valid From**, **Valid Until** și
     o notă; ordinea rândurilor (prin tragere) este ordinea de preferință;
   - apăsați **Save**.
5. Toate alternativele se pot revedea în **Manufacturing → Products → BoM Alternatives**, cu lista de
   materiale, linia și componenta originală.

## 6. Flux de utilizare

### Pasul 1 — Substituirea automată la confirmare

**Manufacturing → Operations → Manufacturing Orders → New**, alegeți produsul cu o componentă setată pe
*Automatic* și cantitatea, apoi **Confirm**.

Ce se întâmplă, pentru fiecare componentă stocabilă cu politică *Automatic*, înainte de rezervare:

1. se folosește întâi stocul liber al componentei originale în locația sursă a comenzii;
2. lipsa se acoperă din alternativele valabile la data de început a comenzii, în ordinea lor, din stocul
   liber al fiecăreia, cu cantitatea convertită după echivalența definită;
3. cu **Partial Substitution** bifat, lipsa se poate împărți între mai multe alternative; fără ea, se
   folosește doar o alternativă care acoperă toată lipsa;
4. pentru fiecare alternativă folosită se adaugă o linie nouă de componentă, iar linia originală rămâne
   cu restul cantității (sau dispare, dacă a fost înlocuită integral); pe comandă se scrie un mesaj de
   forma „2 kg of Rășină A replaced by 2.400 g of Rășină B (Automatic).”.

Componentele deja marcate ca preluate, cele aprovizionate la comandă și cele fără alternative nu se
substituie.

### Pasul 2 — Substituirea automată la verificarea disponibilității

Dacă stocul sosește mai târziu sau se schimbă, **Check Availability** pe comanda confirmată reia
substituirea pentru cantitatea încă lipsă (doar cu **Substitute on Availability Check** bifat).

### Pasul 3 — Substituirea manuală

Pe o comandă în ciornă sau confirmată, în lista componentelor, liniile care au alternative au butonul cu
săgeți (**Substitute**). Apăsați-l; se deschide fereastra **Substitute Component**.

Găsiți pe ecran:

- în stânga: comanda, componenta, cantitatea **To Consume** și cantitatea **Reserved**;
- în dreapta: **Alternative** (doar alternativele valabile la data comenzii), **Quantity to Replace** (din
  componenta originală, propusă ca partea nerezervată) și **Alternative Quantity**, convertită automat;
- dedesubt, tabelul cu fiecare componentă (originala și alternativele): **Needed**, **Free** (stoc liber în
  locația sursă) și **Forecasted** (stoc previzionat), plus nota alternativei.

Verificați că alternativa aleasă are stoc **Free** cel puțin cât **Alternative Quantity** și că
**Quantity to Replace** nu depășește cantitatea de consumat. Apăsați **Substitute**: linia originală
păstrează restul, se adaugă linia alternativei (rezervată), iar pe comandă se scrie mesajul cu motivul
*Manual*. Dacă înlocuirea depășește partea nerezervată, rezervarea originalei se reface pentru rest.

### Pasul 4 — Producerea

Pe linia alternativei, coloana **Replaced Component** arată componenta originală. La **Produce All**,
consumul așteptat ține cont de substituire, deci nu apare avertismentul de consum diferit de rețetă când
s-au consumat cantitățile substituite.

### Pasul 5 — Raportul de substituiri

**Manufacturing → Reporting → Component Substitutions**. Găsiți pe ecran, pe fiecare rând: data, comanda
(**Manufacturing Order**), **Replaced Component**, **Consumed Instead**, cantitatea, unitatea, motivul
(**Substitution**: *Manual* / *Automatic*) și starea mișcării.

Verificați: filtrul **Done** pentru consumurile efective, filtrele **Manual** / **Automatic** după motiv și
gruparea pe **Replaced Component** sau **Consumed Instead**; totalul cantității pe o alternativă
corespunde consumului ei pe comenzile din perioadă. Pentru export, selectați rândurile și **Actions →
Export**.

### Note de monografie și raportare

Modulul nu generează note contabile proprii. Alternativa se consumă la costul ei, prin nota standard a
comenzii de producție, de exemplu:

- consumul componentei alternative: Dr 601 „Cheltuieli cu materiile prime” / Cr 301 „Materii prime”;
- obținerea produsului finit: Dr 345 „Produse finite” / Cr 711 „Venituri aferente costurilor stocurilor
  de produse”.

Diferența de cost dintre componenta originală și alternativă se reflectă în costul produsului finit.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `mrp` | listele de materiale, comenzile de producție, verificarea consumului la **Produce All** |
| `stock` | stocul liber și previzionat, rezervarea componentelor |

**Ce e automat:** substituirea la confirmare și la **Check Availability** pentru componentele *Automatic*,
conversia cantităților, respectarea valabilității și a ordinii alternativelor, mesajul pe comandă,
corecția consumului așteptat.

**Ce rămâne manual:** definirea alternativelor și a echivalențelor, substituirea pe componentele
*Manual*, verificarea raportului.

## 8. Verificări pentru consultant

- [ ] Pe linia listei de materiale, butonul **Alternatives** deschide fereastra în care se adaugă
  alternativele și se alege **Substitution**.
- [ ] O alternativă identică cu componenta originală sau cu produsul fabricat este refuzată.
- [ ] La confirmarea unei comenzi cu stoc insuficient din originală, lipsa este acoperită din
  alternativă, cu cantitatea convertită corect (de exemplu 2 kg → 2.400 g la echivalența 1 kg = 1.200 g).
- [ ] Fără **Partial Substitution**, o alternativă care nu acoperă toată lipsa nu este folosită.
- [ ] O alternativă expirată (**Valid Until** în trecut) nu este propusă.
- [ ] **Check Availability** reia substituirea pentru cantitatea încă lipsă.
- [ ] Fereastra **Substitute Component** arată stocul liber și previzionat al originalei și al
  alternativelor; înlocuirea manuală scrie mesajul *Manual* pe comandă.
- [ ] **Produce All** nu cere confirmarea consumului pentru componentele substituite.
- [ ] **Component Substitutions** listează substituirea, cu componenta înlocuită și motivul.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `A component cannot be an alternative of itself.` | Alternativa este chiar componenta originală | Alegeți alt produs |
| `The product to manufacture cannot be its own alternative component.` | Alternativa este produsul fabricat de listă | Alegeți alt produs |
| `The quantity of an alternative component must be positive.` | **Quantity** este zero sau negativă | Introduceți cantitatea echivalentă |
| `The validity start date must be before the end date.` | **Valid From** este după **Valid Until** | Corectați perioada |
| `You cannot replace more than X <unitate>.` | **Quantity to Replace** depășește cantitatea de consumat neconsumată | Micșorați cantitatea |
| `This alternative is not valid for the component on the order date.` | Alternativa nu este valabilă la data de început a comenzii | Alegeți altă alternativă sau corectați valabilitatea |
| `The component move is already done or cancelled.` | Linia de componentă a fost deja consumată sau anulată | Nu se mai poate substitui |
| `The quantity to replace must be positive.` | **Quantity to Replace** este zero | Introduceți o cantitate |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița, bannerul și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`.
Dacă se doresc capturi, ele se generează cu skill-ul `fisa-screenshots` (setările, fereastra de
alternative a liniei, comanda după substituirea automată, fereastra **Substitute Component**, raportul
**Component Substitutions**) și se leagă apoi în pașii din secțiunea 6.

## 11. Observații pentru manual

- Echivalența cantităților trebuie explicată cu un exemplu: cantitatea alternativei înlocuiește
  cantitatea componentei originale de pe linie, nu o unitate din ea.
- Ordinea alternativelor este ordinea de preferință la substituirea automată.
- Substituirea automată folosește doar stocul liber din locația sursă a comenzii; stocul rezervat pentru
  alte comenzi nu este luat.
