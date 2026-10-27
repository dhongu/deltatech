# Fișă Modul: Proces-verbal de predare-primire a implementării

**Modul:** `deltatech_business_process_handover_document`
**Utilizator principal:** Consultant / manager de proiect de implementare Odoo
**Prioritate:** 🟡 Medie (documentul care închide formal o etapă de implementare și condiționează recepția și facturarea ei)

---

## 1. Scop business

La finalul unei implementări sau al unei etape, furnizorul și beneficiarul semnează un **proces-verbal
de predare-primire** care consemnează ce s-a livrat și ce s-a testat. Fără modul, documentul se
redactează de mână, din liste de procese, teste și dezvoltări ținute în altă parte. Modulul îl generează
ca **PDF** direct din **Proiectul** de implementare (`deltatech_business_process`), cu:

- părțile (companiile, reprezentanții și testerii fiecăreia);
- textul procesului-verbal (starea sistemului, documentație, conturi și acces, teste, responsabilități);
- **Anexa 1** — procesele pe arii, cu numărul de pași de test interni și de acceptanță finalizați;
- lista **dezvoltărilor personalizate** intrate în producție, cu cod, arie și durată.

Documentul poate fi limitat la o singură **etapă de implementare**, ca predarea să acopere exact
etapa recepționată.

## 2. Bază legală și context

Procesul-verbal de predare-primire este documentul justificativ uzual al recepției serviciilor de
implementare (Legea contabilității nr. 82/1991 cere ca operațiunile să fie consemnate în documente
justificative). Modulul **nu** stabilește clauzele contractuale: textul documentului este standard,
iar ce se predă rezultă din datele proiectului. Rolul lui contractual (recepție, termen de garanție,
facturare) se stabilește prin contractul de implementare.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Manager de proiect (furnizor) | Completează părțile, alege etapa, tipărește documentul |
| Consultant | Finalizează testele și pașii lor; marchează ariile verificate |
| Reprezentantul beneficiarului | Semnează documentul |

Nu există grupuri noi; se folosesc drepturile modulului **Business process**. Rol recomandat la
testare: un utilizator cu drept de modificare a proiectelor.

## 4. Conturi și date implicate

Modulul nu postează note contabile. Date folosite, din proiectul de implementare:

- **Informații Furnizor**: **Companie Furnizor**, **Reprezentant Furnizor**, **Testeri Furnizor**;
- **Informații Beneficiar**: **Companie Beneficiar**, **Reprezentant Beneficiar**, **Testeri Beneficiar**;
- **Handover Stage Filter** — etapa de implementare predată (opțională);
- **procesele** proiectului, grupate pe **arii**, și **testele** lor, cu domeniul (**Internal**,
  **User Acceptance**), starea (**Done**) și pașii;
- **dezvoltările** proiectului, cu cod, nume, arie, durată și stare (**Production**);
- bifa **Handover Checked** de pe fiecare arie.

Reprezentanții se aleg dintre persoane (contacte care nu sunt companii).

Date minime pentru demo: un proiect cu un client, două arii (ex. Vânzări, Stocuri), câte două procese
pe arie, un test intern și unul de acceptanță cu pași, finalizate (**Done**), și o dezvoltare în starea
**Production**.

## 5. Configurare inițială

1. Verificați etapele de implementare: **Business process → Configuration → Implementation Stage**.
2. Pe procesele proiectului, completați etapa de implementare, dacă predarea se face pe etape.
3. Creați contactele reprezentanților și testerilor (persoane), la ambele părți.
4. Verificați că testele care trebuie să apară în anexă sunt în starea **Done** și au pași.
5. Verificați că dezvoltările livrate sunt în starea **Production** și au completate codul și durata.

## 6. Flux de utilizare

### Pasul 1 — Completarea părților pe proiect

**Business process → Business process → Projects**, deschideți proiectul. În partea de jos a
formularului, completați:

- în **Informații Furnizor**: **Companie Furnizor**, **Reprezentant Furnizor**, **Testeri Furnizor**;
- în **Informații Beneficiar**: **Companie Beneficiar**, **Reprezentant Beneficiar**, **Testeri Beneficiar**;
- în **Handover Options**: **Handover Stage Filter** — etapa predată, sau gol pentru tot proiectul.

Cu o etapă aleasă, documentul conține doar procesele din acea etapă (cu testele lor) și doar
dezvoltările legate de pașii acestor procese. Fără etapă, conține toate procesele și toate dezvoltările
proiectului.

### Pasul 2 — Marcarea ariilor verificate

**Business process → Configuration → Area**, pe fiecare arie deja recepționată (ex. într-o predare
anterioară), bifați **Handover Checked**. În anexă, coloana de acceptanță a acestor arii apare ca
**N/A**. Bifa este pe arie, deci se aplică tuturor proiectelor care folosesc aria.

### Pasul 3 — Verificarea datelor înainte de tipărire

1. **Găsiți pe ecran** — în proiect, butonul statistic **Developments** și lista de procese; în
   **Business process → Process Tests**, testele proiectului, cu domeniul și starea.
2. **Verificați** — testele care trebuie numărate sunt **Done** și au pași (cele în altă stare nu se
   numără); dezvoltările livrate sunt **Production** (celelalte nu apar în document); procesele au aria
   completată (un proces fără arie nu apare în anexă); etapa din **Handover Stage Filter** e cea
   predată.
3. **Treceți mai departe** — doar după aceste verificări tipăriți documentul.

### Pasul 4 — Tipărirea procesului-verbal

Din proiect, **Acțiuni → Tipărire → Proces verbal** (în engleză: **Print → Handover Document**). Se
descarcă un PDF A4 cu:

- **Proces Verbal de Predare-Primire a Sistemului Odoo**, data curentă și participanții: compania,
  reprezentantul și testerii fiecărei părți;
- textul predării, cu secțiunile **Starea Sistemului**, **Documentație și Resurse**, **Conturi și
  Acces**, **Teste și Verificări**, **Responsabilități ulterioare** și locul pentru semnături;
- **Anexa 1** — pe fiecare arie (rând evidențiat, cu totaluri) și pe fiecare proces: numărul de pași de
  test **Internal** și **User Acceptance** finalizați;
- **Dezvoltări personalizate** — pe arii: **Cod**, **Nume**, **Aria**, **Durată**.

Limba documentului este limba utilizatorului care îl tipărește.

### Note de monografie și raportare

Modulul **nu generează note contabile**. Procesul-verbal semnat poate susține recepția serviciilor și
facturarea etapei, potrivit contractului; înregistrarea contabilă se face separat, la factură.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `deltatech_business_process` | Proiectele, ariile, procesele, testele, dezvoltările și etapele de implementare |

**Ce e automat:** colectarea proceselor, testelor și dezvoltărilor proiectului; filtrarea pe etapă;
numărarea pașilor de test finalizați pe arii și procese; data documentului.

**Ce rămâne manual:** completarea părților, alegerea etapei, marcarea ariilor verificate, semnarea
documentului tipărit.

## 8. Verificări pentru consultant

- [ ] PDF-ul conține compania, reprezentantul și testerii ambelor părți.
- [ ] Anexa 1 are un rând pe fiecare arie și unul pe fiecare proces al ariei.
- [ ] Numărul de pași **Internal** al unui proces este egal cu numărul de pași ai testelor interne
      **Done** ale procesului.
- [ ] Un test care nu este **Done** nu se numără.
- [ ] O arie cu **Handover Checked** are **N/A** la acceptanță.
- [ ] Doar dezvoltările în starea **Production** apar în lista de dezvoltări.
- [ ] Cu **Handover Stage Filter** setat, apar doar procesele etapei și dezvoltările legate de pașii lor.
- [ ] Fără etapă, apar toate procesele și dezvoltările proiectului.
- [ ] Documentul tipărit de un utilizator cu limba română are textul în română.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Un proces lipsește din anexă | Procesul nu are arie sau nu e în etapa aleasă | Completați aria sau etapa procesului |
| Pași de test = 0 | Testele nu sunt **Done** sau nu au pași | Finalizați testele și completați pașii |
| Lista de dezvoltări este goală | Dezvoltările nu sunt în **Production** sau, cu etapă aleasă, nu sunt legate de pașii proceselor din etapă | Actualizați starea sau legați dezvoltarea de pasul procesului |
| Reprezentantul nu se poate alege | Contactul este o companie | Alegeți o persoană de contact |
| Coloana de acceptanță arată **N/A** neașteptat | Aria are **Handover Checked** bifat, de la o predare anterioară | Debifați aria, dacă trebuie din nou recepționată |
| Textul documentului e în engleză | Utilizatorul care tipărește are limba engleză | Tipăriți cu un utilizator cu limba română |

## 10. Capturi de ecran

Fișa este **doar text**, fără capturi. Dacă se vor adăuga, capturile planificate, în ordinea pașilor:

| # | Fișier planificat | Conținut |
|---|---|---|
| 1 | `01_proiect_parti.png` | Proiectul cu **Informații Furnizor**, **Informații Beneficiar** și **Handover Options** |
| 2 | `02_arie_handover_checked.png` | Aria cu bifa **Handover Checked** |
| 3 | `03_pv_pagina1.png` | PDF: prima pagină a procesului-verbal |
| 4 | `04_pv_anexa1.png` | PDF: Anexa 1 cu pașii de test pe arii și procese |
| 5 | `05_pv_dezvoltari.png` | PDF: lista dezvoltărilor personalizate |

Generarea lor se face cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, cu helperul `report_shot` pentru PDF), în română.

## 11. Observații pentru manual

Explicați că procesul-verbal **reflectă datele proiectului**: ce nu e finalizat în Odoo (teste în alte
stări, dezvoltări care nu sunt în producție) nu apare în document, deci verificarea de la pasul 3 se
face înainte de fiecare tipărire. Pentru predările pe etape, recomandați completarea etapei pe toate
procesele încă de la planificare. Atenționați că bifa **Handover Checked** este pe **arie**, nu pe
proiect: la un al doilea proiect care folosește aceeași arie, bifa rămâne și trebuie revizuită. Textul
documentului este fix; dacă beneficiarul cere alte clauze, ele se adaugă manual pe documentul semnat
sau se cere o personalizare a raportului.
