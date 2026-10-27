# Fișă Modul: Registrul de credențiale pentru servicii externe

**Modul:** `deltatech_credentials`
**Utilizator principal:** Administrator Odoo / consultant tehnic
**Prioritate:** 🟢 Scăzută (modul tehnic, folosit ca loc comun pentru datele de acces ale integrărilor)

---

## 1. Scop business

Integrările cu servicii externe (curieri, platforme de plată, API-uri ale furnizorilor) au nevoie de
date de acces: utilizator și parolă, cheie API sau token. Fără un loc comun, aceste date ajung
împrăștiate în parametrii de sistem sau în fișierele de configurare și sunt greu de găsit și de
schimbat. Modulul oferă un **registru unic de credențiale**, vizibil doar administratorilor, în care
fiecare serviciu are o fișă cu nume, un cod de identificare și datele de acces potrivite tipului ales.
Alte module pot citi credențialele după **cod**, fără ca datele să fie scrise în setările lor.

## 2. Bază legală și context

Nu există temei contabil sau fiscal. Contextul este de securitate operațională: datele de acces sunt
date confidențiale, iar accesul la ele se limitează la administratori. Regulamentul (UE) 2016/679
(GDPR) cere măsuri de securitate adecvate pentru datele prelucrate; păstrarea credențialelor într-un
singur loc, cu acces restrâns, ajută la controlul lor.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Administrator (Setări) | Creează, modifică și șterge credențialele |
| Consultant tehnic | Stabilește codul fiecărei credențiale, pe care îl folosește modulul de integrare |
| Ceilalți utilizatori | Nu văd meniul și nu au acces la credențiale |

Roluri recomandate pentru testare: un administrator cu drept **Setări** și un utilizator obișnuit, ca
să se verifice că al doilea nu are acces.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile.

Date minime pentru demo: trei credențiale de test, câte una pentru fiecare tip de acces (de exemplu un
curier cu utilizator și parolă, un serviciu cu cheie API, un serviciu cu token). Folosiți **numai date
de test**, niciodată parole reale, pe o bază de demo.

## 5. Configurare inițială

1. Instalați modulul (depinde doar de `base`).
2. Accesul este dat automat grupului **Administrator** (Setări); nu sunt alte setări.

## 6. Flux de utilizare

> Fișă text: pașii nu au capturi de ecran.

### Pasul 1 — Lista credențialelor

**Setări → Utilizatori și companii → Credentiale** (*Credentials*). Lista arată **Nume** și **Cod**
pentru fiecare credențială; căutarea se face după nume.

### Pasul 2 — Crearea unei credențiale

Apăsați **Nou**. Completați:

- **Nume** (obligatoriu) — numele serviciului, de exemplu „Curier — cont test”;
- **Cod** — un cod scurt, unic în practică, după care modulul de integrare găsește credențiala (de
  exemplu `curier_test`);
- **Tip acces** — alegerea afișează doar câmpurile potrivite:
  - **Utilizator si parola** — **Utilizator** și **Parola** (ascunsă pe ecran);
  - **Client_id si client_secret** — **Id client** și **Secret client / Cheie API**;
  - **Token acces** — **Token acces**.

Salvați.

### Pasul 3 — Schimbarea sau revocarea

Când serviciul extern schimbă parola sau cheia, deschideți credențiala din listă, înlocuiți valoarea și
salvați; modulele care o citesc după cod folosesc imediat valoarea nouă. Pentru revocare, ștergeți
credențiala din **Acțiuni → Șterge**.

### Pasul 4 — Verificarea accesului

1. **Găsiți pe ecran:** autentificați-vă cu un utilizator fără drept de administrator și căutați meniul
   **Credentiale** în **Setări**.
2. **Verificați:** meniul nu apare, iar deschiderea directă a unei credențiale dă eroare de acces.
3. **Treceți mai departe:** abia apoi introduceți credențialele reale pe baza de producție.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr) și nu are rapoarte.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `base` | Meniul **Utilizatori și companii**, grupul **Administrator** |
| Module de integrare | Citesc credențiala după **Cod**; pe 20.0 niciun modul din suită nu o folosește încă |

**Ce e automat:** afișarea câmpurilor după tipul de acces, ascunderea parolei pe ecran, restricția de
acces la administratori.

**Ce rămâne manual:** introducerea și actualizarea datelor de acces, alegerea codului convenit cu
modulul de integrare.

Nu există legături cu declarații ANAF.

## 8. Verificări pentru consultant

- [ ] Meniul **Credentiale** apare în **Setări → Utilizatori și companii** pentru administrator.
- [ ] Schimbarea **Tip acces** afișează doar câmpurile tipului ales.
- [ ] **Parola** apare mascată în formular.
- [ ] Un utilizator fără drept de administrator nu vede meniul și nu poate deschide credențialele.
- [ ] După schimbarea valorii, modulul de integrare (dacă există) folosește valoarea nouă.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Eroare de acces la deschiderea unei credențiale | Utilizatorul nu este administrator | Lucrați din contul unui administrator |
| Câmp obligatoriu lipsă: **Nume** | Credențiala s-a salvat fără nume | Completați **Nume** |
| Integrarea nu găsește credențiala | **Cod** diferit de cel așteptat de modulul de integrare | Corectați **Cod** după documentația integrării |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Dacă se
vor adăuga capturi, ele se generează cu skill-ul `fisa-screenshots` (numai cu date de test) și se leagă
în pașii 1–4 din secțiunea 6.

## 11. Observații pentru manual

- Doar **Parola** este mascată pe ecran; **Secret client / Cheie API** și **Token acces** se văd în clar
  pentru administrator. Manualul recomandă ca ecranul să nu fie partajat sau capturat cu date reale.
- Valorile sunt păstrate în baza de date necriptate; protecția vine din restricția de acces și din
  securitatea bazei și a backup-urilor.
- Unele etichete românești din interfață nu au diacritice (**Credentiale**, **Utilizator si parola**,
  **Parola**); manualul le citează așa cum apar pe ecran.
