# Fișă Modul: Acces pe echipa de vânzări și depozit implicit

**Modul:** `deltatech_sale_team`
**Utilizator principal:** Administrator funcțional (configurare drepturi), șef de echipă de vânzări, agent de vânzări
**Prioritate:** 🟡 Medie (necesar la companiile cu mai multe echipe sau puncte de lucru, unde fiecare echipă trebuie să lucreze doar pe documentele și depozitul ei)

---

## 1. Scop business

În Odoo standard, drepturile de vânzări au două trepte pentru agenți: **doar documentele proprii** sau
**toate documentele**. Între ele lipsește treapta de mijloc, cerută de companiile organizate pe echipe
(sucursale, magazine, canale): **șeful de echipă vede tot ce lucrează echipa lui, dar nu și celelalte
echipe**. Modulul adaugă această treaptă prin grupul **Team Manager** și restrânge, pentru agenții
obișnuiți, și lista de clienți la cei proprii.

În plus, fiecare echipă de vânzări primește un **Depozit implicit**: când pe comandă se alege echipa,
comanda preia automat depozitul echipei, ca livrarea să plece din locul potrivit.

## 2. Bază legală și context

Modul de control intern, fără temei legal sau fiscal. Contextul este segregarea accesului la date
comerciale (comenzi, facturi, clienți) pe structura organizatorică a companiei. Modulul nu generează
documente și nu postează note contabile.

## 3. Utilizatori și roluri

| Grup | Ce vede pe comenzi și analiza vânzărilor | Facturi (citire) | Echipe de vânzări | Clienți |
|---|---|---|---|---|
| **Vânzări: Utilizator: Doar documentele proprii** | standard: comenzile proprii și cele fără vânzător | doar cele proprii sau fără vânzător | toate | doar cei urmăriți, proprii sau fără vânzător |
| **Team Manager** (adăugat de modul) | în plus, comenzile echipei proprii și cele fără echipă (citire, creare, modificare) | ale echipei proprii sau fără echipă | doar echipa proprie | ca agentul |
| **Vânzări: Utilizator: Toate documentele** | toate | toate | toate | ca agentul |
| **Vânzări: Administrator** | toate | toate | toate | toți |

„Echipa proprie” este echipa de vânzări a utilizatorului, adică echipa în care este membru.

**Team Manager** nu are o categorie proprie în formularul utilizatorului: se atribuie din **Setări →
Utilizatori și companii → Grupuri** (cu modul dezvoltator activ), adăugând utilizatorul în grupul
**Team Manager**. Grupul include automat drepturile de agent. Grupul **Toate documentele** include
automat **Team Manager**.

Roluri recomandate la testare: doi agenți în echipe diferite, un șef de echipă membru al uneia dintre
ele și un administrator vânzări.

## 4. Conturi și date implicate

Modulul nu atinge contabilitatea; nu există conturi implicate. Date folosite:

- **Echipele de vânzări**, cu membrii și câmpul nou **Default Warehouse** (Depozit implicit);
- **Depozitele** (cel puțin două, pentru demo);
- **Vânzătorul** și **Echipa de vânzări** de pe comenzi, facturi și clienți.

Date minime pentru demo: două depozite, două echipe („Magazin București” cu depozitul București,
„Magazin Cluj” cu depozitul Cluj), câte un agent în fiecare echipă, un șef de echipă membru în echipa
București și câteva comenzi pe fiecare echipă.

## 5. Configurare inițială

1. Activați **Setări → Inventar → Depozite → Locații de depozitare** și creați depozitele, dacă nu
   există.
2. **Vânzări → Configurare → Echipe de vânzări**: pe fiecare echipă completați **Default Warehouse** și
   adăugați membrii.
3. **Setări → Utilizatori și companii → Utilizatori**: agenților le dați **Vânzări: Utilizator: Doar
   documentele proprii**.
4. Cu modul dezvoltator activ, **Setări → Utilizatori și companii → Grupuri**, deschideți **Team
   Manager** și adăugați șefii de echipă la utilizatori.
5. Verificați că fiecare șef de echipă este membru al **unei singure** echipe — ea devine echipa lui de
   referință.

## 6. Flux de utilizare

### Pasul 1 — Comandă nouă cu depozitul echipei

Agentul deschide **Vânzări → Comenzi → Oferte → Nou**. Echipa de vânzări se completează cu echipa lui;
în fila **Alte informații**, câmpul **Depozit** preia **Default Warehouse** al echipei. Dacă agentul
schimbă echipa pe comandă, depozitul se schimbă odată cu ea. Echipele fără depozit implicit nu modifică
depozitul ales.

### Pasul 2 — Lucrul agentului pe documentele proprii

Agentul vede în **Vânzări → Comenzi → Comenzi** doar comenzile la care este vânzător și pe cele fără
vânzător, iar în
**Vânzări → Comenzi → Clienți** doar clienții pe care îi urmărește, pe care îi are alocați sau care nu
au vânzător. Clienții altor agenți nu apar nici la căutare, nici în selecția de pe comandă.

### Pasul 3 — Lucrul șefului de echipă

Șeful de echipă deschide **Vânzări → Comenzi → Comenzi** și **Raportare → Vânzări**:

1. **Găsiți pe ecran** — grupați lista după **Echipa de vânzări**; apar echipa proprie, comenzile fără
   echipă și eventualele comenzi la care șeful de echipă este el însuși vânzător.
2. **Verificați** — comenzile celorlalte echipe nu apar; totalurile din analiza vânzărilor corespund
   doar echipei proprii; facturile din **Facturare → Clienți → Facturi** sunt doar ale echipei proprii
   sau fără echipă.
3. **Treceți mai departe** — șeful de echipă poate crea și modifica comenzile echipei (inclusiv ale
   colegilor), dar nu le poate șterge.

### Pasul 4 — Vizibilitatea echipelor

În **Vânzări → Configurare → Echipe de vânzări**, șeful de echipă vede doar echipa proprie. Agenții,
utilizatorii cu **Toate documentele** și administratorii văd toate echipele.

### Note de monografie și raportare

Modulul **nu generează note contabile**. Restricțiile se aplică și în analiza vânzărilor, deci
rapoartele unui șef de echipă arată doar cifrele echipei lui.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sales_team` | Echipele de vânzări și grupurile standard de vânzări |
| `sale_stock` | Depozitul comenzii, preluat din echipă |
| `account` | Facturile, restrânse pe echipă / vânzător |
| `stock` | Depozitele |

**Ce e automat:** completarea depozitului din echipă; filtrarea comenzilor, liniilor, analizei
vânzărilor, facturilor, echipelor și clienților după grupul utilizatorului.

**Ce rămâne manual:** alocarea membrilor pe echipe, atribuirea grupului **Team Manager** și alegerea
depozitului implicit pe fiecare echipă.

## 8. Verificări pentru consultant

- [ ] Pe o comandă nouă, alegerea echipei „Magazin Cluj” setează depozitul Cluj.
- [ ] Agentul din București nu vede comenzile agentului din Cluj.
- [ ] Agentul nu vede clienții alocați altui agent, dar vede clienții fără vânzător.
      Accesul prin urmărirea clientului nu e fiabil până la corecția dhongu/deltatech#3535.
- [ ] Șeful de echipă București vede comenzile tuturor agenților din București și pe cele fără echipă,
      dar nu pe cele din Cluj.
- [ ] Șeful de echipă vede în **Echipe de vânzări** doar echipa București.
- [ ] Analiza vânzărilor a șefului de echipă conține doar cifrele echipei lui.
- [ ] Un utilizator cu **Toate documentele** vede comenzile ambelor echipe.
- [ ] Administratorul vânzări vede toți clienții.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Șeful de echipă nu vede comenzile echipei | Nu este membru al echipei sau nu are grupul **Team Manager** | Adăugați-l ca membru și în grup |
| Șeful de echipă vede comenzile tuturor echipelor | Are și grupul **Toate documentele** (sau Administrator) | Scoateți grupul superior |
| Agentul nu găsește un client existent | Clientul are alt vânzător | Alocați clientul agentului sau lăsați-l fără vânzător |
| Agentul nu vede un client pe care îl urmărește (sau vede unul pe care nu îl urmărește) | Ramura „urmăritor” a regulii compară greșit abonarea cu partenerul — problemă cunoscută (dhongu/deltatech#3535) | Până la corecție, nu vă bazați pe urmărire pentru acces; alocați clientul agentului |
| Depozitul nu se schimbă la alegerea echipei | Echipa nu are **Default Warehouse** | Completați depozitul pe echipă |
| Grupul **Team Manager** nu apare în formularul utilizatorului | Grupul nu are categorie proprie | Atribuiți-l din **Grupuri**, cu modul dezvoltator activ |

## 10. Capturi de ecran

Fișa este **doar text**, fără capturi. Dacă se vor adăuga, capturile planificate, în ordinea pașilor:

| # | Fișier planificat | Conținut |
|---|---|---|
| 1 | `01_echipa_depozit.png` | Formularul echipei de vânzări cu **Default Warehouse** |
| 2 | `02_comanda_depozit.png` | Comanda nouă cu depozitul preluat din echipă |
| 3 | `03_lista_sef_echipa.png` | Lista de comenzi a șefului de echipă, grupată pe echipă |

Generarea lor se face cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în română.

## 11. Observații pentru manual

Prezentați drepturile ca pe o **scară cu patru trepte** (proprii → echipă → toate → administrator) și
puneți tabelul din secțiunea 3 în manual: e întrebarea cea mai frecventă a clienților. Atrageți atenția
că, odată instalat modulul, **agenții văd doar clienții proprii sau fără vânzător** — o schimbare
vizibilă față de Odoo standard, care trebuie anunțată echipei înainte de punerea în producție. Explicați
că depozitul implicit al echipei este doar o propunere: operatorul îl poate schimba pe comandă.
