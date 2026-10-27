# Fișă Modul: Ordinea cronologică a facturilor și modificarea numărului

**Modul:** `deltatech_invoice_number`
**Utilizator principal:** Contabil / operator facturare
**Prioritate:** 🔴 Ridicată (numerotarea și datarea facturilor emise sunt controlate de inspecția fiscală)

---

## 1. Scop business

Facturile emise trebuie să aibă numere în ordine și date care nu „sar înapoi”: o factură nu poate
purta o dată mai veche decât factura emisă înaintea ei în aceeași serie. Odoo standard permite
confirmarea unei facturi cu o dată anterioară ultimei facturi din jurnal. Modulul:

- **blochează confirmarea** unei facturi către client (sau a unei note de credit) dacă în același jurnal
  există deja o factură confirmată cu o dată mai nouă, și avertizează operatorul încă de la alegerea
  jurnalului;
- permite unui **grup dedicat de utilizatori** să **modifice numărul** unei facturi (de exemplu după o
  migrare de date sau pentru a corecta o factură numerotată greșit), cu actualizarea referinței pe
  liniile notei contabile.

## 2. Bază legală și context

Codul fiscal (Legea 227/2015), **art. 319**, cere ca factura să aibă un număr de ordine, în baza uneia
sau mai multor serii, care identifică factura în mod unic. Controlul ordinii cronologice pe jurnal
(serie) ajută la respectarea acestei cerințe și la evitarea golurilor sau a inversărilor de date
semnalate la control. Modificarea numărului unei facturi deja emise trebuie folosită cu grijă: factura
transmisă clientului sau în RO e-Factura păstrează numărul inițial.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Operator facturare | Emite facturi; primește avertizarea sau blocarea când data nu respectă ordinea |
| Manager contabilitate | Activează controlul pe jurnalele de vânzări |
| Utilizator cu grupul **Permite modificarea numărului de factură** | Schimbă numărul unei facturi din meniul **Acțiuni** al facturii |

Roluri recomandate pentru testare: un utilizator **Facturare** fără grupul de modificare (vede doar
blocarea) și un administrator cu grupul tehnic **Permite modificarea numărului de factură** bifat pe
fișa utilizatorului (Setări → Utilizatori → utilizatorul → drepturile tehnice).

## 4. Conturi și date implicate

Modulul nu creează note contabile și nu folosește conturi proprii; se aplică facturilor către clienți
(**4111** / **707** / **4427**) și notelor de credit.

Date minime pentru demo:

- jurnalul de vânzări **Facturi clienți**;
- un client și un produs;
- o factură confirmată cu data de 15 ale lunii.

## 5. Configurare inițială

1. **Facturare / Contabilitate → Configurare → Jurnale** → deschideți jurnalul de vânzări.
2. În tabul **Note contabile** (*Journal Entries*), grupul **Numerotare facturi** (vizibil doar pe
   jurnalele de tip vânzări), bifați **Restricționează data facturii**.
3. Opțional, alegeți o **Secvență jurnal** (vezi secțiunea 11).
4. Salvați. Pentru modificarea numerelor, bifați grupul **Permite modificarea numărului de factură**
   pe utilizatorii care au voie s-o facă.

## 6. Flux de utilizare

> Fișă text: pașii nu au capturi de ecran.

### Pasul 1 — Avertizare la alegerea jurnalului

**Facturare → Clienți → Facturi** → **Nou**. Completați clientul și **Data facturii** = 10 ale lunii
(anterioară facturii confirmate din 15). La alegerea (sau schimbarea) jurnalului apare o fereastră de
avertizare: „Înregistrați factura cu o dată egală sau ulterioară datei <15 ale lunii>”. Factura se poate
în continuare salva în ciornă.

### Pasul 2 — Blocarea confirmării

Apăsați **Confirmă**. Confirmarea este refuzată cu același mesaj, cât timp există în jurnal o factură
de același tip, confirmată, cu o dată mai nouă. Corectați **Data facturii** la 15 sau după și confirmați
din nou: factura primește următorul număr din serie.

Controlul se face separat pe tip de document: facturile se compară cu facturile, notele de credit cu
notele de credit, și doar în jurnalul ales.

### Pasul 3 — Modificarea numărului unei facturi

Deschideți factura, apoi din meniul **Acțiuni** (rotița din formular) alegeți **Modifică numărul
facturii**. Opțiunea apare doar pentru utilizatorii cu grupul **Permite modificarea numărului de
factură**.

În fereastra **Modifică numărul facturii**, câmpul **Număr factură** este precompletat cu numărul
actual. Introduceți numărul nou și apăsați **Aplică** (sau **Anulează**).

Ce se întâmplă: factura primește numărul nou. Pe facturile către clienți, **Referința** facturii și
referința tuturor liniilor din nota contabilă devin noul număr. Pe facturile de furnizor, liniile notei
primesc ca referință numărul facturii furnizorului (câmpul **Referință factură**), sau numărul nou dacă
acela lipsește.

### Pasul 4 — Verificarea după modificare

1. **Găsiți pe ecran:** în lista **Facturi**, căutați numărul nou; în tabul **Elemente jurnal**, coloana
   **Referință**.
2. **Verificați:** numărul nou apare o singură dată în jurnal; liniile notei au referința nouă; nu a
   rămas un gol în serie (numărul vechi nu este folosit de altă factură).
3. **Treceți mai departe:** abia apoi retipăriți factura sau o retransmiteți, dacă e cazul.

### Note de monografie și raportare

Modulul nu generează și nu modifică note contabile (Dr/Cr): nota facturii rămâne cea standard
(de exemplu 4111 = 707 + 4427). Se schimbă doar numărul documentului și referința liniilor, care apar în
jurnalul de vânzări, în D394 și în SAF-T cu numărul nou.

## 7. Legături cu alte module / declarații

| Modul / declarație | Rol |
|---|---|
| `account` | Facturi, jurnale, secvențe |
| Jurnal de vânzări, D394, SAF-T | Preiau numărul facturii; după modificare, numărul nou |
| RO e-Factura | Factura deja transmisă păstrează la ANAF numărul inițial; modificarea nu o retransmite |

**Ce e automat:** avertizarea la alegerea jurnalului, blocarea confirmării, actualizarea referinței
liniilor după modificarea numărului.

**Ce rămâne manual:** activarea controlului pe fiecare jurnal, acordarea grupului de modificare,
alegerea numărului nou.

## 8. Verificări pentru consultant

- [ ] Pe jurnalul de vânzări apare grupul **Numerotare facturi**; pe jurnalele de cumpărări sau bancă
  nu apare.
- [ ] Cu **Restricționează data facturii** bifat, o factură datată înaintea ultimei facturi confirmate
  primește avertizare la alegerea jurnalului și nu se poate confirma.
- [ ] Cu bifa scoasă, aceeași factură se confirmă fără mesaj.
- [ ] O notă de credit nu este blocată de o factură cu dată mai nouă (se compară doar cu notele de
  credit).
- [ ] **Modifică numărul facturii** apare în **Acțiuni** doar pentru utilizatorii din grup.
- [ ] După **Aplică**, factura și liniile notei au numărul nou ca referință.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `Înregistrați factura cu o dată egală sau ulterioară datei ...` | Există în jurnal o factură confirmată cu dată mai nouă | Corectați **Data facturii** sau verificați factura cu data mai nouă |
| Opțiunea **Modifică numărul facturii** lipsește din **Acțiuni** | Utilizatorul nu are grupul de modificare | Bifați grupul **Permite modificarea numărului de factură** |
| Eroare de unicitate sau de secvență la **Aplică** | Numărul nou este deja folosit sau nu respectă formatul seriei | Alegeți un număr liber, în formatul seriei |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Dacă se
vor adăuga capturi, ele se generează cu skill-ul `fisa-screenshots` și se leagă în pașii 1–4 din
secțiunea 6.

## 11. Observații pentru manual

- Câmpul **Secvență jurnal** este folosit de numerotarea unei facturi în ciornă din secvența
  jurnalului, descrisă în `readme/DESCRIPTION.md`. În versiunea 19.0 această numerotare nu are buton în
  interfață (se apelează doar din cod), deci manualul nu o prezintă ca pas pentru operator.
- Controlul cronologic se aplică doar facturilor și notelor de credit **către clienți**; facturile de
  furnizor nu sunt verificate.
- Modificarea numărului unei facturi deja trimise clientului sau în RO e-Factura trebuie însoțită de o
  procedură internă (notă explicativă, eventual stornare și refacturare).
