# Fișă Modul: Loturi de transferuri pregătite din comenzi

**Modul:** `deltatech_batch_transfer`
**Utilizator principal:** Gestionar / operator depozit
**Prioritate:** 🟡 Medie (accelerează recepțiile și livrările grupate; nu are efect contabil propriu)

---

## 1. Scop business

Când un furnizor aduce marfa pentru mai multe comenzi de achiziție sau un client ridică marfa pentru
mai multe comenzi de vânzare, gestionarul vrea să lucreze **un singur document** (un lot de
transferuri), nu câte o recepție sau o livrare pe comandă. Modulul extinde loturile standard Odoo:

- asistentul **Prepare batch** adună într-un lot toate recepțiile sau livrările deschise ale unui
  partener și poate completa direct cantitățile efective dintr-o listă de produse (de exemplu din avizul
  furnizorului);
- la validarea lotului, transferurile la care nu s-a introdus nicio cantitate nu mai sunt validate ca
  „goale”, ci sunt scoase din lot (sau păstrate pentru mai târziu, după un parametru);
- câmpuri de identificare pe lot (**Reference**, **Note**, **Direction**), o pagină **Received** cu
  liniile efectiv primite, un buton **Add to batch** pe transfer și raportul **Deliveries**, care
  tipărește toate avizele lotului odată.

## 2. Bază legală și context

Modulul nu generează documente contabile proprii. Recepțiile și livrările validate din lot sunt
transferurile standard Odoo; NIR-ul și avizul de însoțire a mărfii rămân documentele fiecărui transfer.
Contextul este operațional: evitarea validării unor transferuri fără cantități (care, în Odoo, ar fi
tratate ca livrate integral sau ar cere confirmări) și reducerea timpului de lucru la rampa de
recepție/livrare.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Gestionar / operator depozit | Pregătește lotul, introduce cantitățile, validează lotul, tipărește avizele |
| Agent de vânzări | Pornește **Prepare batch** din lista comenzilor de vânzare |
| Consultant / administrator | Activează loturile în setări, decide valoarea parametrului `deltatech_batch_keep_pickings` |

Roluri recomandate pentru testare: **Inventory / User** cu loturile activate și **Sales / User** pentru
pornirea din comenzile de vânzare.

## 4. Conturi și date implicate

Modulul nu folosește conturi proprii. În evaluarea perpetuă a stocului, transferurile validate din lot
generează notele standard ale recepției și livrării (vezi „Note de monografie”).

Date minime pentru demo:

- un furnizor cu două comenzi de achiziție confirmate (deci două recepții deschise);
- un client cu două comenzi de vânzare confirmate și stoc disponibil;
- doi-trei produse stocabile.

## 5. Configurare inițială

1. Instalați modulul `deltatech_batch_transfer` (depinde de `stock`, `sale_stock`, `purchase_stock`).
2. **Inventory → Configuration → Settings**, secțiunea operațiunilor: bifați **Batch, Wave & Cluster
   Transfers** și salvați. Fără această setare nu apare meniul loturilor.
3. Opțional, **Settings → Technical → System Parameters**: parametrul `deltatech_batch_keep_pickings`.
   - lipsă (implicit, recomandat) — la validare, transferurile fără cantități sunt **scoase** din lot;
   - `True` — transferurile fără cantități **rămân** în lot, nevalidate, pentru procesare ulterioară (nu
     se recomandă cu interfața de coduri de bare).

## 6. Flux de utilizare

### Pasul 1 — Pregătirea lotului din meniu

**Inventory → Operations → Prepare batch**. Se deschide asistentul, în care completați:

- **Partner** — furnizorul sau clientul ale cărui transferuri deschise se grupează;
- **Responsible** — utilizatorul responsabil de lot;
- **Reference** — o referință liberă (de exemplu numărul avizului furnizorului);
- **Mode** — *Purchase* (recepții) sau *Sale* (livrări);
- **Set Done Qty** — bifat, cantitățile devin cantități efective (pregătite); nebifat, se păstrează
  rezervarea fără a marca nimic ca efectuat;
- lista de produse (doar în modul *Purchase*) — produs și cantitate, pentru a limita lotul la ce a sosit
  efectiv.

Apăsați **Confirm**. Asistentul caută comenzile partenerului care au transferuri în așteptare, confirmate
sau gata, păstrează doar recepțiile (modul *Purchase*) sau livrările (modul *Sale*), creează lotul cu
direcția și referința completate, îl confirmă, verifică disponibilitatea și îl deschide.

Cu lista de produse completată, cantitățile se repartizează pe liniile lotului, în unitatea fiecărei
linii. Dacă un produs din listă nu se găsește în transferurile partenerului, asistentul se oprește cu
eroare; ce depășește cantitățile deschise nu se repartizează.

Dacă partenerul nu are niciun transfer deschis de tipul ales, asistentul rămâne deschis, fără lot creat.

### Pasul 2 — Pregătirea lotului din comenzile de vânzare

**Sales → Orders → Orders**, în listă selectați una sau mai multe comenzi ale **aceluiași client**, apoi
**Actions → Prepare batch**. Asistentul se deschide cu clientul completat și modul *Sale*; lotul se
creează doar din livrările comenzilor selectate. Apăsați **Confirm**.

### Pasul 3 — Adăugarea unui transfer la un lot

Deschideți un transfer (**Inventory → Operations → Transfers → Receipts** sau **Deliveries**) care nu
este într-un lot și apăsați **Add to batch**. Se deschide dialogul standard **Add to batch**, în care
alegeți un lot existent sau creați unul nou, apoi **Confirm**. Pe un transfer care este deja într-un lot,
butonul afișează eroarea „This picking is already in a batch”.

### Pasul 4 — Citirea lotului

**Inventory → Operations → Jobs → Batch Transfers**, deschideți lotul. Găsiți pe ecran:

1. lângă tipul operației, **Reference**; sub data planificată, **Note** și **Direction** (*Incoming* /
   *Outgoing*, doar citire);
2. pe loturile de recepție confirmate, pagina **Received**, cu liniile care au cantitate mai mare decât
   zero;
3. în lista operațiilor, liniile cu cantitate sunt îngroșate, iar cele cu cantitate zero sunt estompate.

Verificați că **Direction** corespunde modului ales, că în **Received** apar exact produsele sosite și că
liniile estompate sunt cele care chiar lipsesc.

### Pasul 5 — Validarea lotului

Introduceți sau corectați cantitățile (manual sau cu scanerul) și apăsați **Validate**.

- Fără parametrul `deltatech_batch_keep_pickings`: transferurile la care nicio linie nu are cantitate
  sunt **scoase din lot** înainte de validare; celelalte se validează normal. Transferurile scoase rămân
  deschise și pot fi adăugate la alt lot.
- Cu parametrul `deltatech_batch_keep_pickings` = `True`: transferurile fără cantitate **rămân în lot**,
  dar nu se validează. Dacă niciun transfer nu are cantitate, apare eroarea „No effective quantities
  set”.

La anularea unui lot (**Cancel**), transferurile sunt eliberate din lot.

### Pasul 6 — Tipărirea avizelor

Din lot, **Print → Deliveries**. Se generează un singur PDF cu documentul de livrare standard al fiecărui
transfer din lot, unul după altul. Verificați în PDF că sunt toate transferurile lotului, în ordinea din
lot.

### Note de monografie și raportare

Modulul nu generează note contabile proprii. În evaluarea perpetuă (automată), fiecare transfer validat
din lot generează notele standard, de exemplu:

- recepție de mărfuri: Dr 371 „Mărfuri” / Cr 408 „Furnizori – facturi nesosite” (sau contul de stoc în
  tranzit configurat);
- livrare de mărfuri: Dr 607 „Cheltuieli privind mărfurile” / Cr 371 „Mărfuri”.

Transferurile scoase din lot sau rămase nevalidate nu generează note.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `stock` | loturile de transferuri (în Odoo 20 incluse în `stock`), dialogul **Add to batch**, documentul de livrare |
| `purchase_stock` | recepțiile comenzilor de achiziție, sursa modului *Purchase* |
| `sale_stock` | livrările comenzilor de vânzare, sursa modului *Sale* și acțiunea din lista comenzilor |

**Ce e automat:** găsirea transferurilor deschise ale partenerului, crearea și confirmarea lotului,
verificarea disponibilității, repartizarea cantităților din listă, scoaterea transferurilor goale la
validare, eliberarea transferurilor la anularea lotului.

**Ce rămâne manual:** alegerea partenerului și a modului, introducerea cantităților efective (dacă nu
s-a folosit lista), validarea lotului, procesarea ulterioară a transferurilor scoase din lot.

## 8. Verificări pentru consultant

- [ ] **Inventory → Operations → Prepare batch** cu un furnizor cu două recepții deschise creează un
  singur lot cu ambele recepții, **Direction** *Incoming* și referința completată.
- [ ] Cu lista de produse și **Set Done Qty**, liniile lotului au exact cantitățile din listă; un produs
  care nu e la acel furnizor oprește asistentul cu mesaj.
- [ ] Din lista comenzilor de vânzare, **Prepare batch** pe comenzi ale aceluiași client creează lotul
  din livrările lor; pe comenzi ale unor clienți diferiți apare eroarea „Please select orders for the
  same customer.”.
- [ ] Pagina **Received** apare pe loturile de recepție confirmate și arată doar liniile cu cantitate.
- [ ] La **Validate**, un transfer fără nicio cantitate este scos din lot și rămâne deschis.
- [ ] Cu `deltatech_batch_keep_pickings` = `True`, transferul fără cantitate rămâne în lot, nevalidat.
- [ ] **Print → Deliveries** produce un PDF cu avizele tuturor transferurilor din lot.
- [ ] La anularea lotului, transferurile nu mai au lot.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `Please select orders for the same customer.` | Comenzi de vânzare ale unor clienți diferiți selectate pentru **Prepare batch** | Selectați doar comenzile unui singur client |
| `The product [cod]nume was not found for this partner.` | Un produs din lista asistentului nu se află în transferurile deschise ale partenerului | Scoateți produsul din listă sau verificați comanda |
| `No effective quantities set` | Cu `deltatech_batch_keep_pickings` activ, niciun transfer din lot nu are cantitate | Introduceți cantitățile înainte de **Validate** |
| `This picking is already in a batch` | **Add to batch** apăsat pe un transfer care are deja lot | Scoateți transferul din lotul vechi sau lucrați în acel lot |
| Asistentul rămâne deschis, fără lot | Partenerul nu are transferuri deschise de tipul ales | Verificați partenerul, modul și starea comenzilor |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița, bannerul și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`.
Dacă se doresc capturi, ele se generează cu skill-ul `fisa-screenshots` (asistentul **Prepare batch**,
lotul creat cu pagina **Received**, butonul **Add to batch**, validarea, PDF-ul **Deliveries**) și se
leagă apoi în pașii din secțiunea 6.

## 11. Observații pentru manual

- Manualul trebuie să spună că loturile apar doar după activarea **Batch, Wave & Cluster Transfers** și
  că meniul lor este **Inventory → Operations → Jobs → Batch Transfers**.
- Comportamentul la validare (scoaterea transferurilor goale) este diferit de cel standard Odoo și
  trebuie explicat operatorilor, ca să nu caute transferurile „dispărute” din lot.
- Lista de produse din asistent este disponibilă doar în modul *Purchase*.
