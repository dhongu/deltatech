# Fișă Modul: Etichete de raft din documentul de modificare preț

**Modul:** `deltatech_price_change_label`
**Utilizator principal:** Gestionar de magazin (schimbă etichetele de pe raft după o modificare de
preț), responsabil de prețuri (întocmește documentul de modificare)
**Prioritate:** 🟡 Medie (la fiecare actualizare de prețuri în comerțul cu amănuntul, fără efect
contabil)

---

## 1. Scop business

După o modificare de prețuri, magazinul trebuie să schimbe etichetele de pe raft pentru toate
produsele afectate, cu prețul nou cu TVA. Fără ajutor, gestionarul caută produsele unul câte unul
și tipărește etichetele separat. Modulul este **puntea** dintre documentul **Modificare preț
produs** (`deltatech_price_change`) și asistentul de etichete (`deltatech_product_labels`): pe
document apare butonul **Tipărește etichete**, care deschide asistentul cu **toate produsele din
document** deodată, cu depozitul documentului și cu un format nou, **Etichetă de raft cu preț**,
care arată numele produsului, prețul cu TVA, codul și unitatea de măsură.

## 2. Bază legală și context

- Modulul **nu are efect fiscal sau contabil**: nu creează documente, nu modifică prețuri și nu
  modifică stocul.
- **OG nr. 99/2000** și **HG nr. 947/2000** — la vânzarea către consumatori, prețul se afișează la
  raft **cu toate taxele incluse**. De aceea eticheta **Etichetă de raft cu preț** tipărește prețul
  cu TVA și mențiunea „TVA inclus”. Prețul unitar pe kg/l, unde este cerut, nu se calculează de
  modul.
- Procesul-verbal de modificare a prețurilor și eventuala notă contabilă a diferenței sunt descrise
  în fișa modulului `deltatech_price_change`.

## 3. Utilizatori și roluri

| Rol | Ce poate face |
|---|---|
| Utilizator care vede documentele de modificare preț (cel puțin **Vânzări: Utilizator: Numai documente proprii**) | apasă **Tipărește etichete** și tipărește etichetele |
| **Vânzări: Administrator** | creează și confirmă documentele de modificare preț (modulul `deltatech_price_change`) |

Roluri recomandate pentru testare:
- un **administrator vânzări**, care întocmește documentul de modificare;
- un **gestionar de magazin** cu drept de citire în Vânzări, care doar tipărește etichetele.

## 4. Conturi și date implicate

Modulul **nu generează note contabile** și nu atinge conturi. Date minime pentru demo (aceleași ca în
fișa `deltatech_price_change`):

| Produs | Referință internă | Preț vechi | Preț nou | Preț nou cu TVA 21% |
|---|---|---|---|---|
| Cană ceramică 350 ml | CAN-350 | 35,00 | 39,00 | 47,19 lei |
| Termos inox 0,5 l | TRM-050 | 79,00 | 89,00 | 107,69 lei |

- depozitul **Magazin Centru** (cod `MAG`);
- documentul de modificare preț **CLP000001**, tip **Din modificările de preț**, depozitul Magazin
  Centru, cu cele două produse.

## 5. Configurare inițială

1. Instalați `deltatech_price_change` și `deltatech_product_labels`. Modulul
   `deltatech_price_change_label` **se instalează singur** când ambele sunt instalate.
2. Configurați taxa de vânzare pe produse (TVA 21% în exemplu): eticheta calculează prețul cu TVA din
   taxele de vânzare ale produsului.
3. Verificați formatul de hârtie al imprimantei: **Etichetă de raft cu preț** are etichete de
   7 × 3,5 cm, așezate una lângă alta pe formatul de hârtie implicit al companiei (de regulă A4).

## 6. Flux de utilizare

### Pasul 1 — Butonul „Tipărește etichete” pe documentul de modificare preț

Deschideți documentul din **Vânzări → Produse → Modificare preț produs** (de exemplu CLP000001).
În antetul documentului, lângă **Confirmă**, apare butonul **Tipărește etichete**. El apare doar
când documentul are linii, deci și pe **Ciornă**; tipăriți etichetele după confirmare, când lista
produselor este definitivă.

### Pasul 2 — Asistentul „Etichete produs” deschis din document

Apăsați **Tipărește etichete**. Se deschide fereastra **Etichete produs**, completată singură:

- **Format** — **Etichetă de raft cu preț**, propus implicit; se poate alege orice alt format de
  etichetă din `deltatech_product_labels` (de exemplu coala A4 3x8 sau etichetele termice);
- **Depozit** — depozitul documentului (**Magazin Centru**);
- **Listă de prețuri** — lăsați-o goală: cu o listă de prețuri aleasă, eticheta arată prețul din
  listă și nu mai corespunde procesului-verbal;
- câte o linie pentru **fiecare produs** din document, cu **Nr. etich.** = 1 și **Preț** = prețul
  de vânzare curent al produsului, **fără TVA**.

**Verificați:** fiecare produs apare o singură dată, chiar dacă are mai multe linii în document (de
exemplu, două modificări în zile diferite). Dacă o linie a documentului este pe un **șablon** de
produs cu variante, asistentul propune câte o linie pentru **fiecare variantă**.

Modificați **Nr. etich.** dacă produsul stă în mai multe locuri pe raft, apoi apăsați **Tipărește**.

### Pasul 3 — Etichetele de raft tipărite

Se generează un PDF cu câte o etichetă pentru fiecare unitate din **Nr. etich.**. Fiecare etichetă
are, de sus în jos: **numele produsului**, **prețul cu TVA**, mare, aliniat la dreapta, cu simbolul
monedei, iar jos **referința internă** (sau codul de bare, dacă referința lipsește) și, în dreapta,
**unitatea de măsură** urmată de „· TVA inclus”.

**Găsiți pe etichete:** cana cu **47,19 lei**, termosul cu **107,69 lei**.

**Verificați:** prețul de pe fiecare etichetă este egal cu coloana **Preț nou cu TVA** din
procesul-verbal de modificare a prețurilor (fișa `deltatech_price_change`, pasul 6). Abia apoi
tipăriți pe hârtia de etichete și înlocuiți etichetele de pe raft.

### Note de monografie și raportare

Modulul **nu înregistrează nicio notă contabilă**. Diferența de preț pentru marfa în stoc (la
magazinele cu evidență la preț de vânzare) se tratează în documentul de modificare preț, nu aici.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux |
|---|---|
| `deltatech_price_change` | documentul **Modificare preț produs**, cu produsele și depozitul |
| `deltatech_product_labels` | asistentul **Etichete produs**, formatele de etichete și calculul prețului cu TVA |

Ce este automat: instalarea modulului lângă cele două module, lista produselor din document (fără
dubluri, cu toate variantele unui șablon), depozitul documentului, formatul **Etichetă de raft cu
preț**.

Ce rămâne manual: corectarea **Nr. etich.**, alegerea altui format, tipărirea și schimbarea fizică
a etichetelor de pe raft.

## 8. Verificări pentru consultant

- [ ] Modulul s-a instalat singur după instalarea `deltatech_price_change` și
      `deltatech_product_labels`.
- [ ] Butonul **Tipărește etichete** apare pe un document cu linii și lipsește pe un document gol.
- [ ] Asistentul propune formatul **Etichetă de raft cu preț** și depozitul documentului.
- [ ] Un produs cu două linii în document apare o singură dată în asistent.
- [ ] O linie pe un șablon cu trei variante dă trei linii în asistent.
- [ ] Pe etichete, cana are 47,19 lei și termosul 107,69 lei, egale cu prețurile cu TVA din
      procesul-verbal.
- [ ] Eticheta are mențiunea „TVA inclus” lângă unitatea de măsură.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Butonul **Tipărește etichete** lipsește | Documentul nu are linii, sau `deltatech_product_labels` nu este instalat | Aduceți liniile în document; instalați `deltatech_product_labels` (puntea se instalează singură) |
| Prețul de pe etichetă diferă de procesul-verbal | În asistent este aleasă o **Listă de prețuri**, sau produsul are altă taxă de vânzare | Goliți **Listă de prețuri**; verificați taxa de vânzare a produsului |
| Prețul de pe etichetă este fără TVA (egal cu prețul de listă) | Produsul nu are nicio taxă de vânzare | Completați taxa de vânzare pe produs |
| Etichetele se decalează pe coală | Formatul de hârtie al imprimantei nu corespunde (eticheta are 7 × 3,5 cm) | Folosiți hârtie de etichete potrivită sau alegeți un format cu dimensiune fixă (A4 3x8, termice) |

## 10. Capturi de ecran

Fișa este, deocamdată, **doar text**: nu are capturi de ecran. Capturile planificate, în ordinea
pașilor din secțiunea 6:

1. `01_document_buton_etichete.png` — documentul CLP000001, cu butonul „Tipărește etichete”.
2. `02_asistent_etichete.png` — asistentul „Etichete produs” cu formatul „Etichetă de raft cu preț”.
3. `03_etichete_raft.png` — etichetele de raft tipărite, cu prețurile cu TVA 47,19 și 107,69 lei.

Ele se pot genera ulterior cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`; captura 3 din randarea HTML a raportului), în limba
română, după care se leagă în pașii din secțiunea 6.

## 11. Observații pentru manual

Descrieți modulul în capitolul despre modificarea prețurilor, ca ultimul pas al fluxului: prețul
se schimbă, se întocmește documentul și procesul-verbal, apoi **Tipărește etichete** dă etichetele
noi pentru toate produsele dintr-un singur gest. Insistați pe verificarea prețului de pe etichetă
cu procesul-verbal și pe lăsarea goală a listei de prețuri. Modulul nu are meniu propriu și nu
trebuie instalat separat.
