# Fișă Modul: Pigment RAL pe comanda de producție

**Modul:** `deltatech_ral`
**Utilizator principal:** Planificator producție, operator producție, responsabil nomenclator produse
**Prioritate:** 🟢 Scăzută (specific producătorilor care vopsesc același produs în mai multe culori RAL)

---

## 1. Scop business

Producătorii de tâmplărie, mobilier metalic, profile sau alte produse vopsite în câmp electrostatic
fabrică același produs în zeci de culori RAL. Cu Odoo standard, ar trebui câte o listă de materiale
pentru fiecare culoare, diferită doar prin pigment. Modulul permite **o singură listă de materiale** cu
un pigment generic („RAL 0000”), înlocuit pe fiecare comandă de producție cu **pigmentul real**, ales
automat după culoarea variantei produse sau manual de planificator. Culoarea aleasă se trece și pe
**lotul** produsului finit, ca să se știe ulterior în ce RAL a fost vopsit fiecare lot.

## 2. Bază legală și context

Modul de producție, fără temei legal sau fiscal. Contextul este de trasabilitate: lotul produsului
finit păstrează culoarea RAL folosită, util la reclamații, la livrări parțiale și la refacerea unei
comenzi în aceeași nuanță.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Responsabil nomenclator | Creează pigmentul generic „RAL 0000”, pigmenții reali și atributul de culoare al produselor |
| Inginer de produs | Pune pigmentul generic în lista de materiale |
| Planificator producție | Creează comanda de producție; verifică sau schimbă pigmentul |
| Operator producție | Produce comanda; lotul primește culoarea RAL |

Nu există grupuri noi. Roluri recomandate la testare: **Producție: Administrator** pentru configurare
și **Producție: Utilizator** pentru flux.

## 4. Conturi și date implicate

Modulul nu postează note contabile proprii. Date folosite:

- **Pigmentul generic** — un produs cu **Referință internă** exact `RAL 0000`;
- **Pigmenții reali** — produse cu **Referință internă** `RAL <culoare>` (ex. `RAL Alb`, `RAL 9016`);
- **Atributul de culoare** al produsului finit — un atribut cu tipul de afișare **Culoare**, ale cărui
  valori au aceleași nume ca partea de după „RAL ” din referința pigmenților;
- **Lista de materiale** a produsului finit, cu pigmentul generic ca **componentă**;
- câmpul **RAL** de pe comanda de producție și de pe lot.

Date minime pentru demo: atributul „Culoare” (afișare Culoare) cu valorile „Alb” și „Gri”; produsul
„Profil vopsit” cu variantele Alb și Gri; pigmenții `RAL 0000`, `RAL Alb`, `RAL Gri` (stocabili, cu
stoc); lista de materiale a profilului cu 0,2 kg `RAL 0000`.

## 5. Configurare inițială

1. **Inventar → Produse → Produse**: creați pigmentul generic (ex. „Pigment RAL generic”) cu **Referință
   internă** = `RAL 0000`.
2. Creați pigmenții reali, cu **Referință internă** = `RAL ` + numele culorii, scris exact ca valoarea
   atributului (ex. `RAL Alb` pentru valoarea „Alb”; se ține cont de literele mari și mici).
3. **Inventar → Configurare → Atribute** (cu variantele activate din **Setări → Inventar → Produse**):
   creați atributul de culoare, cu **Tip afișare** = **Culoare**, și valorile lui.
4. Pe produsul finit, adăugați atributul de culoare în fila **Atribute și variante**.
5. **Producție → Produse → Liste de materiale**: creați lista de materiale pe șablonul produsului finit
   (fără variantă) și adăugați ca **componentă** pigmentul generic `RAL 0000`, cu cantitatea consumată.
6. Opțional, pentru a trece culoarea pe lot: activați **Setări → Inventar → Loturi și numere de serie**
   și setați urmărirea pe lot la produsul finit.

## 6. Flux de utilizare

### Pasul 1 — Comanda de producție cu pigmentul ales automat

**Producție → Operațiuni → Comenzi de producție → Nou**, alegeți varianta „Profil vopsit (Alb)”. După
salvare, câmpul **RAL** (sub **Produs**) este completat cu `RAL Alb`, iar în fila **Componente** linia
pigmentului generic a fost înlocuită cu `RAL Alb`, la aceeași cantitate.

### Pasul 2 — Verificarea și schimbarea pigmentului

1. **Găsiți pe ecran** — câmpul **RAL** din antetul comenzii și, în fila **Componente**, linia
   pigmentului.
2. **Verificați** — pigmentul din **RAL** corespunde culorii variantei; în **Componente** nu mai apare
   `RAL 0000`; cantitatea pigmentului este cea din lista de materiale, înmulțită cu cantitatea de
   produs.
3. **Treceți mai departe** — dacă trebuie altă nuanță, alegeți alt pigment în **RAL** (câmpul se poate
   modifica doar cât comanda este **Ciornă** sau **Confirmată**); componenta se schimbă imediat.
   Înlocuirea rezistă și la modificarea cantității de produs.

### Pasul 3 — Confirmarea și producția

**Confirmă**, apoi produceți comanda ca de obicei. Din stoc se consumă pigmentul real, nu cel generic.

### Pasul 4 — Lotul produsului finit

La generarea lotului produsului finit pe comandă (butonul de generare lot/serie), lotul primește
pigmentul în câmpul **RAL**. Lotul se vede în **Inventar → Produse → Loturi/Numere de serie**, unde
câmpul **RAL** apare și ca coloană în listă, lângă **Referință internă**.

### Note de monografie și raportare

Modulul nu are note proprii; la producție, Odoo înregistrează notele standard ale comenzii de
producție (pe evaluare automată, consumul de materii prime și producția obținută), cu singura diferență
că materia primă consumată este **pigmentul real**, evaluat la costul lui. Costul produsului finit
include astfel costul pigmentului folosit efectiv, nu al celui generic.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `mrp` | Comenzile de producție și listele de materiale |
| `stock` | Loturile produsului finit și stocul pigmenților |

**Ce e automat:** alegerea pigmentului după culoarea variantei, la crearea comenzii; înlocuirea
pigmentului generic din componente; păstrarea înlocuirii la recalcularea componentelor; trecerea
culorii pe lotul generat.

**Ce rămâne manual:** crearea pigmenților cu referințe corecte; corectarea pigmentului pe comandă când
nu se potrivește automat.

## 8. Verificări pentru consultant

- [ ] Comanda pentru varianta Alb are **RAL** = `RAL Alb` și componenta `RAL Alb`.
- [ ] Schimbarea manuală a **RAL** pe o comandă în ciornă schimbă componenta.
- [ ] Modificarea cantității de produs păstrează pigmentul real în componente.
- [ ] Pe o comandă finalizată, câmpul **RAL** nu mai poate fi modificat.
- [ ] Un produs fără atribut de culoare are **RAL** gol, iar componenta generică rămâne neschimbată.
- [ ] Lotul generat pe comandă are **RAL** = pigmentul comenzii.
- [ ] Consumul de stoc este pe pigmentul real, nu pe `RAL 0000`.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| **RAL** rămâne gol la crearea comenzii | Atributul nu are tipul de afișare **Culoare** sau nu există pigment cu referința `RAL <valoare>` | Corectați tipul atributului sau referința pigmentului |
| Se alege un pigment greșit | Mai mulți pigmenți au în referință textul `RAL <valoare>` (ex. `RAL Alb` și `RAL Alb mat`) | Folosiți referințe unice, care nu se conțin una pe alta |
| Componenta `RAL 0000` nu se înlocuiește | Pigmentul generic nu are referința exact `RAL 0000` | Corectați referința internă |
| Lipsă stoc la `RAL 0000` | Comanda nu are **RAL** completat | Alegeți pigmentul în **RAL** înainte de confirmare |
| **RAL** nu se poate modifica | Comanda a trecut de starea **Confirmată** | Schimbarea pigmentului se face înainte de începerea producției |

## 10. Capturi de ecran

Fișa este **doar text**, fără capturi. Dacă se vor adăuga, capturile planificate, în ordinea pașilor:

| # | Fișier planificat | Conținut |
|---|---|---|
| 1 | `01_lista_materiale_ral0000.png` | Lista de materiale cu componenta `RAL 0000` |
| 2 | `02_comanda_productie_ral.png` | Comanda de producție cu **RAL** și componenta înlocuită |
| 3 | `03_lot_ral.png` | Lotul produsului finit cu câmpul **RAL** |

Generarea lor se face cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în română.

## 11. Observații pentru manual

Puneți în manual **convenția de codificare** ca regulă de nomenclator: `RAL 0000` pentru pigmentul
generic, `RAL ` + numele valorii de culoare pentru fiecare pigment real — totul depinde de ea, iar
greșelile de scriere (spațiu lipsă, literă mare) sunt cauza tuturor cazurilor de „nu se completează
singur”. Explicați că lista de materiale se face **o singură dată**, pe șablonul produsului, cu
pigmentul generic, și că pigmentul real se vede pe fiecare comandă de producție. Eticheta câmpului
**RAL** este aceeași în română și engleză.
