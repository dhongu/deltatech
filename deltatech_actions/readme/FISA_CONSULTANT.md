# Fișă Modul: Curățarea programată a bazei de date

**Modul:** `deltatech_actions`
**Utilizator principal:** Administrator Odoo / consultant tehnic
**Prioritate:** 🟡 Medie (șterge date definitiv când rularea de test este oprită; nu are efect contabil)

---

## 1. Scop business

O bază Odoo folosită ani de zile acumulează fișiere și mesaje care nu mai sunt necesare: PDF-uri de
factură și de comandă regenerabile, etichete AWB ale curierilor (zeci de GB pe instanțele mari), XML-uri
EDI duplicate, mesaje vechi în chatter. Ele măresc spațiul ocupat, durata backup-urilor și costul
găzduirii. Modulul oferă un set de **curățări programate**, toate pornite și reglate dintr-un singur
loc din **Setări**, cu **rulare de test** care arată ce s-ar șterge înainte de a șterge ceva. Pe lângă
curățări, are acțiuni de întreținere a contactelor (unirea duplicatelor, normalizarea formei juridice
din nume), crearea regulilor de reaprovizionare lipsă și o metodă de anulare forțată a unei comenzi de
vânzare.

## 2. Bază legală și context

Legea contabilității nr. 82/1991 cere păstrarea documentelor justificative și a registrelor contabile
pe perioada prevăzută de lege. Curățările modulului șterg doar **copii regenerabile** (PDF-uri generate
din document, etichete AWB recuperabile de la curier) și **mesaje** din chatter; documentele EDI/ANAF
(XML, ZIP) și atașamentele la care factura trimite direct nu se șterg. Decizia de a șterge mesaje vechi
pe anumite modele rămâne a firmei: modelele care trebuie să-și păstreze istoricul se trec la **Modele
excluse**.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Administrator (Setări) | Activează curățările, reglează parametrii, rulează **Rulează acum** |
| Consultant tehnic | Dimensionează curățările în rulare de test, confirmă cu clientul ce se șterge, creează acțiunea de anulare forțată |
| Contabil / operator | Nu folosește modulul direct; vede doar efectele (PDF-uri regenerate la cerere) |

Roluri recomandate pentru testare: un administrator cu drept **Setări**. Curățările pot fi pornite doar
de administratori și de planificatorul Odoo; ceilalți utilizatori primesc eroare de acces.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile și nu creează note contabile.

Date minime pentru demo:

- câteva facturi și comenzi de vânzare cu PDF-uri generate (tipărite sau trimise pe e-mail) mai vechi
  decât pragul de zile;
- livrări finalizate cu etichetă AWB (dacă se testează curățarea etichetelor);
- mesaje vechi în chatter;
- doi parteneri persoană cu același e-mail sau două firme cu același CUI (pentru unirea duplicatelor).

## 5. Configurare inițială

1. Instalați modulul. Toate acțiunile programate sunt **oprite** la instalare, iar cele care șterg date
   au **Rulare de test** bifată.
2. Deschideți **Setări → Setări generale**, secțiunea **Curățare bază de date** (vizibilă doar
   administratorilor).
3. Pentru fiecare curățare dorită, reglați parametrii (vezi pasul 2) înainte de a o activa.

## 6. Flux de utilizare

> Fișă text: pașii nu au capturi de ecran.

### Pasul 1 — Secțiunea Curățare bază de date

**Setări → Setări generale → Curățare bază de date.** Fiecare curățare este o setare cu bifa în titlu;
bifa pornește sau oprește acțiunea programată corespunzătoare. Curățările disponibile:

| Setare | Ce face | Acțiune programată |
|---|---|---|
| **Atașamente XML duplicate** | Șterge XML-urile EDI/UBL duplicate de pe aceeași factură; păstrează cea mai recentă copie | *Delete duplicate xml attachments* |
| **Curățare PDF-uri de factură** | Șterge PDF-urile de factură generate, inclusiv cele atașate e-mailurilor trimise | *Delete pdf invoice attachments* |
| **Curățare PDF-uri de comandă de vânzare** | Șterge PDF-urile de ofertă / comandă generate | *Delete pdf sale order attachments* |
| **Curățare etichete AWB** | Golește eticheta AWB de pe livrările vechi | *Delete pdf pickings attachments* |
| **Curățare mesaje vechi** | Șterge mesajele vechi din chatter și atașamentele lor (fără XML/ZIP) | *Delete mail messages* |
| **Contacte duplicate** | Unește persoanele cu același e-mail | *Merge duplicate contacts by email* |
| **Companii duplicate** | Unește firmele cu același CUI | *Merge duplicate companies by VAT* |
| **Reguli de reaprovizionare lipsă** | Creează reguli de reaprovizionare pentru produsele stocabile fără reguli | *Create missing reordering rules (0/0)* |
| **Normalizează numele companiilor** | Uniformizează forma juridică din nume (srl → S.R.L., sa → S.A., pfa → P.F.A., ii → I.I.), câte 500 pe rulare | *Normalize company names* |

### Pasul 2 — Reglarea parametrilor

Sub fiecare curățare care șterge date:

- **Rulare de test (nu șterge nimic)** — bifată implicit; acțiunea doar consemnează în jurnalul
  serverului ce ar șterge;
- **Facturi pe rulare** / **Atașamente pe rulare** / **Mesaje pe rulare** — câte înregistrări se
  prelucrează la o rulare;
- **Mai vechi de (zile)** — pragul de vechime (implicit 30 de zile la XML, 90 la PDF-uri și mesaje, 180
  la etichetele AWB);
- **Model de nume** / **Model de subiect** — filtru SQL `LIKE` pe numele atașamentului sau subiectul
  mesajului; gol = toate;
- la XML: **Duplicate minime** și **Ștergeri maxime pe factură**;
- la AWB: **Doar livrările finalizate (efectuate)** și **Doar livrările anulate**, bifate implicit, ca o
  livrare în curs să nu fie atinsă niciodată;
- la mesaje: **Modele excluse** (implicit `business.%,project.%,helpdesk.%`), care își păstrează tot
  istoricul.

La unirea duplicatelor se reglează **Grupuri de contacte pe rulare** și **Grupuri de companii pe
rulare**. Acestea **nu** au rulare de test.

### Pasul 3 — Dimensionarea cu Rulează acum, în rulare de test

Cu **Rulare de test** bifată, apăsați **Rulează acum** sub curățare și confirmați mesajul. Setările se
salvează, curățarea rulează imediat, iar rezultatul apare ca notificare:

1. **Găsiți pe ecran:** notificarea **Rulare de test** cu textul „S-ar șterge N înregistrări (X MB). Nu
   s-a șters nimic.”
2. **Verificați:** numărul și dimensiunea sunt plauzibile față de volumul bazei; dacă sunt prea mari,
   măriți pragul de zile sau restrângeți modelul de nume și rulați din nou. Pentru etichetele AWB,
   confirmați cu curierul cât timp păstrează etichetele, ca să poată fi regenerate.
3. **Treceți mai departe:** abia când rezultatul este cel așteptat, debifați **Rulare de test**.

Unirea contactelor și a companiilor nu are buton **Rulează acum**, intenționat: șterge date fără cale de
întoarcere și rulează doar programat.

### Pasul 4 — Activarea și rularea reală

Bifați titlul curățării și salvați. Sub ea apare **Următoarea execuție**, data la care rulează acțiunea
programată; se poate schimba direct aici. O curățare oprită de la instalare are o dată veche și rulează
la primul ciclu al planificatorului după activare; mutați data înainte dacă vreți să pornească mai
târziu.

**Rulează acum** cu **Rulare de test** debifată șterge imediat și afișează notificarea **Curățare
efectuată**: „S-au șters N înregistrări (X MB).” Ștergerea este definitivă.

Dacă ștergerea este refuzată (de exemplu de regula altui modul), rezultatul nu se raportează ca
șters:

- la curățarea XML, factura cu problema este sărită, celelalte se curăță, iar notificarea
  **Cleanup partly done** adaugă „N records could not be deleted (see the server log).”;
- la celelalte curățări, notificarea roșie **Cleanup failed** („Nothing was deleted: <eroare>”) rămâne
  pe ecran până la închidere; curățarea este anulată în întregime, dar setările salvate se păstrează.

Aceste mesaje nu au încă traducere și apar în engleză.

### Pasul 5 — Copii restaurate (staging)

Pe o copie restaurată din producție toate acțiunile programate sunt oprite, cu excepția curățării
automate a Odoo (*auto-vacuum*). Setarea **Run cleanups from the auto-vacuum job** (fără traducere)
face ca PDF-urile de factură, de comandă și etichetele AWB să fie curățate și de această acțiune, cu
aceleași praguri și aceeași rulare de test. Pe baza de producție, setarea rămâne debifată.

### Pasul 6 — Anularea forțată a unei comenzi de vânzare (opțional)

Modulul are o metodă care anulează o comandă confirmată împreună cu livrările, mișcările de stoc și
notele contabile legate de ele, **fără verificările obișnuite**. Din motive de siguranță nu are buton;
se activează manual:

1. **Setări → Tehnic → Acțiuni → Acțiuni server** → **Nou**.
2. Model **Comandă de vânzare**, tip **Executare cod Python**, cod
   `record.force_cancel_order_and_moves()`.
3. Opțional, adăugați acțiunea în meniul **Acțiuni** al comenzii și restrângeți-o la un grup de
   administratori.

### Note de monografie și raportare

Curățările nu generează note contabile. Anularea forțată (pasul 6) trece în starea **Anulat** notele
contabile de evaluare a stocului ale livrărilor (de exemplu 607 = 371 la descărcarea din gestiune), fără
note de stornare; folosiți-o doar pe comenzi ale căror livrări nu trebuie să rămână în contabilitate
și verificați apoi fișa contului 371 și stocul.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `account_edi`, `sale`, `sale_stock`, `stock`, `product` | Documentele curățate și modelele pe care rulează acțiunile |
| `deltatech_delivery` | Regenerează eticheta AWB de la curier când a fost ștearsă |
| `deltatech_auto_reorder_rule` | Necesar pentru **Reguli de reaprovizionare lipsă** |
| Contacte (unirea partenerilor) | Asistentul standard Odoo de unire a contactelor, folosit de **Contacte duplicate** și **Companii duplicate** |

**Ce e automat:** rularea programată a curățărilor active, protecția documentelor EDI/ANAF și a
atașamentelor principale ale facturii, notificarea rezultatului la **Rulează acum**.

**Ce rămâne manual:** alegerea curățărilor, a pragurilor și momentul în care se oprește rularea de test;
crearea acțiunii de anulare forțată; confirmarea cu curierul a perioadei de păstrare a etichetelor.

## 8. Verificări pentru consultant

- [ ] După instalare, toate curățările sunt oprite și cele care șterg date au **Rulare de test**
  bifată.
- [ ] Secțiunea **Curățare bază de date** nu apare pentru un utilizator fără drept de administrator.
- [ ] **Rulează acum** în rulare de test arată numărul și dimensiunea și nu șterge nimic (PDF-urile
  rămân pe facturi).
- [ ] Cu rularea de test oprită, aceeași curățare șterge exact numărul anunțat.
- [ ] XML-urile EDI ale facturii nu se șterg; din duplicatele aceleiași facturi rămâne cea mai recentă
  copie.
- [ ] Mesajele de pe modelele din **Modele excluse** rămân neatinse.
- [ ] Etichetele AWB de pe livrările în curs nu se șterg; pe o livrare curățată, eticheta se regenerează
  la cerere.
- [ ] O ștergere refuzată dă **Cleanup failed** (sau **Cleanup partly done** la XML) și nu e numărată
  ca ștearsă.
- [ ] **Următoarea execuție** apare doar după activarea curățării și poate fi modificată.
- [ ] Unirea companiilor după CUI lasă un singur partener pe fiecare CUI.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `Only administrators can run the database cleanup.` | Curățarea a fost pornită de un utilizator fără drept de administrator | Rulați din contul unui administrator |
| `Cleanup failed` — `Nothing was deleted: ...` | Ștergerea a fost refuzată (regulă de acces sau constrângere a altui modul); nu s-a șters nimic | Citiți eroarea și jurnalul serverului, remediați cauza, rulați din nou |
| `Cleanup partly done` — `N records could not be deleted (see the server log).` | La curățarea XML, atașamentele unor facturi nu s-au putut șterge | Verificați facturile din jurnalul serverului; celelalte au fost curățate |
| „S-ar șterge 0 înregistrări” | Pragul de zile sau modelul de nume exclud tot | Verificați pragul și modelul; un model de nume îngust (ex. `Label%`) prinde doar o parte din etichetele AWB |
| Eticheta AWB nu se mai poate regenera | Curierul nu mai păstrează eticheta pentru expedierile vechi | Măriți pragul de zile; confirmați perioada de păstrare cu curierul |
| Curățarea nu rulează pe copia de test | Copia restaurată are acțiunile programate oprite | Bifați **Run cleanups from the auto-vacuum job** pe copie |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Dacă se
vor adăuga capturi, ele se generează cu skill-ul `fisa-screenshots` și se leagă în pașii 1–6 din
secțiunea 6.

## 11. Observații pentru manual

- Regula de aur pentru manual: **întâi rulare de test cu Rulează acum, apoi activare**. Ștergerea reală
  nu se poate anula.
- Unirea contactelor și a companiilor nu are rulare de test; se activează doar după ce s-a verificat
  manual o mostră de duplicate.
- Anularea forțată ocolește regulile Odoo și anulează note contabile fără stornare; manualul o prezintă
  ca procedură de excepție, rezervată administratorilor.
- Numele acțiunilor programate (*Delete pdf invoice attachments* etc.) apar în engleză în **Setări →
  Tehnic → Automatizare → Acțiuni programate**; setările din **Curățare bază de date** sunt traduse.
