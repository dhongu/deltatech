# Fișă Modul: Culori pe categoriile de produse

**Modul:** `deltatech_product_category_color`
**Utilizator principal:** Gestionar / operator de depozit (recunoaște din priviri ce fel de marfă are
un transfer), administrator de nomenclator (alege culorile categoriilor)
**Prioritate:** 🟢 Scăzută (ajutor vizual, fără efect asupra stocului sau a contabilității)

---

## 1. Scop business

Într-un depozit cu multe recepții și livrări pe zi, operatorul vrea să știe dintr-o privire ce fel
de marfă conține fiecare transfer: produse congelate, chimicale, piese grele, marfă fragilă. Odoo
nu arată categoriile produselor pe cardurile transferurilor. Modulul dă fiecărei **categorii de
produse** o **culoare** și afișează pe fiecare card din vizualizarea **Kanban** a transferurilor
etichete colorate cu categoriile produselor din transfer. Astfel echipa își poate împărți munca
(de exemplu, „transferurile cu eticheta albastră merg la camera frigorifică”) fără să deschidă
fiecare document.

## 2. Bază legală și context

- Modulul **nu are efect fiscal sau contabil**: nu creează documente, nu modifică stocul și nu
  schimbă categoria produselor.
- Culoarea este doar o informație de afișare. Contul de stoc, metoda de evaluare și rutele rămân
  cele din categoria produsului, ca în Odoo standard.

## 3. Utilizatori și roluri

| Rol | Ce poate face |
|---|---|
| **Produse: Creează** (în **Date de bază**) | modifică categoriile de produse, deci și culoarea lor |
| **Inventar: Utilizator** | vede etichetele colorate pe cardurile transferurilor |

Roluri recomandate pentru testare:
- un utilizator cu **Produse: Creează**, care alege culorile categoriilor;
- un **operator de depozit** (Inventar: Utilizator), care urmărește transferurile în Kanban.

## 4. Conturi și date implicate

Modulul **nu generează note contabile** și nu atinge conturi. Date minime pentru demo:

| Categorie | Culoare aleasă | Produs din exemplu |
|---|---|---|
| Toate / Alimente congelate | albastru | Mazăre congelată 1 kg |
| Toate / Detergenți | roșu | Detergent lichid 5 l |
| Toate / Ambalaje | verde | Cutie carton 40×30 |

- o recepție de la furnizorul **Frig Distribuție SRL** cu mazăre congelată și cutii de carton;
- o livrare către **Casa Verde SRL** cu detergent lichid;
- o livrare încă nerezervată (fără stoc disponibil), cu mazăre congelată.

## 5. Configurare inițială

1. Instalați `deltatech_product_category_color` (dependențe: `product`, `stock`). Nu e nevoie de
   altă setare.
2. La instalare, fiecare categorie existentă primește o culoare **aleasă la întâmplare**; la fel
   orice categorie creată ulterior. Treceți prin categorii (secțiunea 6, pasul 1) și alegeți culori
   care au un sens pentru echipă.
3. Stabiliți cu echipa depozitului semnificația culorilor (de exemplu, albastru = marfă congelată)
   și treceți-o în procedura internă.

## 6. Flux de utilizare

### Pasul 1 — Alegerea culorii unei categorii

Deschideți **Inventar → Configurare → Categorii de produse** și alegeți categoria (de exemplu
„Toate / Alimente congelate”). În formular, sub **Părinte**, apare câmpul **Index culoare**, cu
paleta de culori Odoo. Apăsați pe culoarea dorită (albastru); formularul se salvează ca de obicei.

Repetați pentru celelalte categorii din exemplu: roșu pentru „Detergenți”, verde pentru „Ambalaje”.
Prima căsuță a paletei înseamnă **fără culoare**: categoria apare atunci pe carduri ca etichetă gri.

### Pasul 2 — Etichetele colorate pe cardurile transferurilor

Deschideți **Inventar → Operații → Transferuri** (sau **Recepții** ori **Livrări**) și treceți pe
vizualizarea **Kanban** din dreapta sus. Fiecare card de transfer are, sub starea lui, câte o
etichetă pentru fiecare categorie a produselor din transfer, în culoarea categoriei.

**Găsiți pe ecran:** pe cardul recepției de la Frig Distribuție SRL, etichetele „Alimente congelate”
(albastru) și „Ambalaje” (verde); pe cardul livrării către Casa Verde SRL, eticheta „Detergenți”
(roșu).

**Verificați:**
- fiecare categorie apare **o singură dată** pe card, chiar dacă transferul are mai multe produse
  din aceeași categorie;
- livrarea nerezervată are și ea eticheta „Alimente congelate”: categoriile se iau din liniile
  transferului (produsele cerute), nu din cantitățile rezervate;
- un produs a cărui linie a fost anulată nu mai aduce eticheta categoriei lui.

### Pasul 3 — Schimbarea culorii și efectul pe carduri

Dacă schimbați culoarea unei categorii (pasul 1), toate cardurile transferurilor care conțin
produse din ea își schimbă imediat culoarea etichetei, inclusiv transferurile deja finalizate. Nu e
nevoie de nicio actualizare a transferurilor.

### Note de monografie și raportare

Modulul **nu înregistrează nicio notă contabilă** și nu adaugă rapoarte. Etichetele apar doar în
vizualizarea Kanban a transferurilor; lista și formularul transferului rămân ca în Odoo standard.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux |
|---|---|
| `product` | categoriile de produse, unde se alege culoarea |
| `stock` | transferurile (recepții, livrări, transferuri interne) și vizualizarea lor Kanban |

Ce este automat: culoarea inițială a fiecărei categorii (aleatoare), lista categoriilor de pe fiecare
transfer, actualizarea etichetelor când se schimbă culoarea sau liniile transferului.

Ce rămâne manual: alegerea culorilor cu sens pentru echipă și convenția internă despre ce înseamnă
fiecare culoare.

## 8. Verificări pentru consultant

- [ ] Formularul categoriei are câmpul **Index culoare**, cu paleta de culori.
- [ ] O categorie nouă primește singură o culoare.
- [ ] În **Inventar → Operații → Transferuri**, vizualizarea **Kanban**, recepția de la Frig
      Distribuție SRL are etichetele „Alimente congelate” (albastru) și „Ambalaje” (verde).
- [ ] Livrarea nerezervată are eticheta categoriei produsului cerut.
- [ ] Două produse din aceeași categorie dau o singură etichetă pe card.
- [ ] După anularea unei linii, categoria ei dispare de pe card (dacă nu mai e alt produs din ea).
- [ ] Schimbarea culorii unei categorii se vede imediat pe toate cardurile.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Etichetele nu apar pe transferuri | Transferurile sunt afișate ca **listă**, nu ca **Kanban** | Treceți pe vizualizarea **Kanban** din dreapta sus |
| Eticheta categoriei e gri | Categoria are prima căsuță a paletei (fără culoare) | Alegeți o culoare în **Index culoare** |
| Două categorii au aceeași culoare | Culorile inițiale sunt alese la întâmplare, iar paleta are puține culori | Alegeți manual culori diferite pentru categoriile importante |
| Nu se poate modifica culoarea | Utilizatorul nu are drept de modificare a categoriilor de produse | Cereți dreptul **Produse: Creează** (fila **Drepturi de acces** a utilizatorului, categoria **Date de bază**) |

## 10. Capturi de ecran

Fișa este, deocamdată, **doar text**: nu are capturi de ecran. Capturile planificate, în ordinea
pașilor din secțiunea 6:

1. `01_categorie_culoare.png` — formularul categoriei „Alimente congelate”, cu câmpul „Index culoare”.
2. `02_transferuri_kanban.png` — transferurile în Kanban, cu etichetele colorate ale categoriilor.

Ele se pot genera ulterior cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în limba română, după care se leagă în pașii din
secțiunea 6.

## 11. Observații pentru manual

Prezentați modulul ca un **cod de culori pentru depozit**: culoarea se alege o singură dată, pe
categorie, și apare apoi singură pe fiecare transfer. Insistați pe faptul că etichetele se văd doar
în **Kanban** și că acoperă și transferurile nerezervate. Recomandați clientului să stabilească în
scris semnificația culorilor, ca toată echipa să le citească la fel.
