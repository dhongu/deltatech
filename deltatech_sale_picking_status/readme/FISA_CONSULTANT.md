# Fișă Modul: Starea livrării pe comenzile de vânzare

**Modul:** `deltatech_sale_picking_status`
**Utilizator principal:** Agent de vânzări / responsabil logistică (urmărirea livrărilor)
**Prioritate:** 🟢 Scăzută (îmbunătățire de vizibilitate peste un câmp standard)

---

## 1. Scop business

Agentul de vânzări trebuie să știe rapid care comenzi au fost livrate, care sunt livrate parțial și
care încă așteaptă. Odoo calculează standard **Starea livrării** (*Delivery Status*) a comenzii din
transferurile de livrare, dar o ascunde în liste și nu oferă filtre gata făcute. Modulul:

- afișează **Starea livrării** ca etichetă colorată în lista de oferte și în lista de comenzi;
- adaugă filtrele **Livrare în curs**, **Livrat parțial**, **Livrat în întregime** și gruparea după
  **Stare livrare**;
- înregistrează în discuția comenzii fiecare schimbare a stării livrării.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale și nu generează note contabile. Contextul este
operațional: urmărirea comenzilor nelivrate și a celor livrate parțial, de exemplu înainte de
facturare sau la discuțiile cu clientul.

Până la versiunea 19 modulul calcula propriul câmp **Picking Status** (Done / In Progress). Începând
cu 20.0 folosește câmpul standard; la actualizare, filtrele salvate, șabloanele de export și
grupările pe vechiul câmp sunt mutate automat pe **Starea livrării**.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Agent de vânzări | Filtrează și grupează comenzile după starea livrării, vede istoricul în discuție |
| Responsabil logistică / depozit | Validează livrările; starea comenzii se actualizează automat |
| Manager de vânzări | Urmărește comenzile rămase nelivrate |

Modulul nu adaugă grupuri sau drepturi. Roluri recomandate pentru testare: un agent de vânzări și un
utilizator de depozit care validează livrările.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile. Date minime pentru demo:

- un produs stocabil cu stoc disponibil (ex. 10 bucăți);
- trei comenzi de vânzare confirmate: una nelivrată, una livrată parțial (livrare cu restanță),
  una livrată integral.

Valorile **Stării livrării** (calculate de Odoo din livrări):

| Valoare | Semnificație | Culoare în listă |
|---|---|---|
| *Not Delivered* | nicio cantitate livrată | albastru |
| *Started* | livrare începută | albastru |
| **Livrat parțial** (*Partially Delivered*) | o parte din cantitate livrată | portocaliu |
| **Livrat în întregime** (*Fully Delivered*) | toată cantitatea livrată | verde |

## 5. Configurare inițială

1. Instalați modulul `deltatech_sale_picking_status` (depinde de `sale_stock` și `mail_tracking`).
2. Nu sunt setări de făcut: coloana, filtrele și urmărirea în discuție sunt active imediat.
3. La actualizarea de pe 19.0, verificați în jurnalul serverului avertismentele despre filtre sau
   vizualizări modificate manual care mai folosesc `picking_status`; acestea trebuie rescrise pe
   **Starea livrării**.

## 6. Flux de utilizare

### Pasul 1 — Confirmarea comenzii și livrarea

Agentul confirmă comenzile în **Vânzări → Comenzi → Oferte**. Depozitul validează livrările din
**Inventar → Operațiuni → Livrări**: una parțial (cu restanță), una integral, una rămâne nevalidată.
**Starea livrării** a fiecărei comenzi se recalculează automat la validarea livrării.

### Pasul 2 — Lista de comenzi cu starea livrării

Agentul deschide **Vânzări → Comenzi → Comenzi** (sau **Oferte**).

1. **Găsește pe ecran** — coloana **Stare livrare**, cu eticheta colorată (în lista de oferte apare
   înaintea coloanei **Stare facturare**); coloana se poate ascunde din selectorul de coloane.
2. **Verifică** — comanda livrată integral are eticheta verde *Fully Delivered*, cea livrată parțial
   portocaliu *Partially Delivered*, cea nelivrată albastru *Not Delivered*.
3. **Treci mai departe** — aplicați filtrele din Pasul 3.

### Pasul 3 — Filtre și grupare

În bara de căutare, meniul de filtre conține, după filtrul **Comenzile mele**:

- **Livrare în curs** — comenzile nelivrate, începute sau livrate parțial;
- **Livrat parțial** — doar comenzile livrate parțial;
- **Livrat în întregime** — comenzile livrate complet.

În **Grupare după** apare **Stare livrare**. Verificați că numărul de comenzi din fiecare grup
corespunde situației livrărilor din Pasul 1. Lista filtrată se poate exporta cu **Acțiuni → Export**.

### Pasul 4 — Istoricul în discuția comenzii

Deschideți o comandă livrată parțial și apoi integral. În discuția comenzii apare, la fiecare
schimbare, o urmărire de tipul *Not Delivered → Partially Delivered → Fully Delivered*, cu data și
utilizatorul care a validat livrarea.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr). Descărcarea din gestiune la livrare (607 = 371) o face
fluxul standard de stoc, independent de acest modul.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale_stock` | calculează **Starea livrării** din livrări |
| `mail_tracking` | urmărirea schimbărilor de stare în discuția comenzii |

**Ce e automat:** calculul stării, afișarea în liste, urmărirea în discuție, migrarea filtrelor
salvate de pe vechiul câmp.

**Ce rămâne manual:** validarea livrărilor; rescrierea vizualizărilor personalizate care mai folosesc
vechiul câmp (semnalate în jurnalul serverului).

## 8. Verificări pentru consultant

- [ ] Coloana **Stare livrare** apare în listele de oferte și comenzi, cu culorile corecte.
- [ ] Filtrul **Livrare în curs** arată comenzile nelivrate și pe cele livrate parțial, nu și pe cele
  livrate integral.
- [ ] Filtrul **Livrat parțial** arată doar comenzile cu restanță.
- [ ] Filtrul **Livrat în întregime** arată doar comenzile livrate complet.
- [ ] Gruparea **Stare livrare** împarte corect comenzile.
- [ ] Validarea unei livrări adaugă în discuția comenzii schimbarea stării.
- [ ] După actualizarea de pe 19.0, un filtru favorit pe „Picking Status” funcționează pe noua stare.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| `View … uses the removed field picking_status, replace it with delivery_status` (jurnal server) | O vizualizare modificată în baza de date folosește vechiul câmp | Înlocuiți `picking_status` cu `delivery_status` în acea vizualizare |
| `Filter … on sale.order still uses picking_status …` (jurnal server) | Un filtru salvat are o condiție care nu a putut fi convertită automat | Refaceți filtrul pe **Stare livrare** |
| Coloana lipsește | A fost ascunsă din selectorul de coloane | Reafișați **Stare livrare** |
| Starea rămâne *Not Delivered* deși marfa a plecat | Livrarea nu a fost validată în Inventar | Validați livrarea |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Capturile
pentru lista colorată, filtre și istoricul din discuție (pașii 2–4) se pot genera ulterior cu skill-ul
`fisa-screenshots`.

## 11. Observații pentru manual

- Pentru utilizatorii obișnuiți cu 19.0: vechea coloană **Picking Status** a fost înlocuită de
  **Stare livrare**; *Done* corespunde lui *Fully Delivered*, *In Progress* lui *Not Delivered /
  Started / Partially Delivered*.
- Culorile etichetelor sunt un ajutor vizual rapid; de menționat semnificația lor în manual.
