# Fișă Modul: Numărarea liniilor de cod din modulele instalate

**Modul:** `deltatech_line_counter`
**Utilizator principal:** Administrator Odoo / consultant tehnic (estimări de efort, audit de migrare)
**Prioritate:** 🟢 Scăzută (unealtă tehnică de administrare, fără impact asupra fluxurilor de business)

---

## 1. Scop business

Înainte de o migrare, de un audit sau de o ofertă de mentenanță, consultantul are nevoie de o măsură
rapidă a mărimii modulelor instalate. Modulul adaugă un asistent care numără liniile de cod din
modulele alese și afișează un tabel cu numărul de linii pe fiecare modul și totalul, direct din
interfața Odoo, fără acces la serverul de fișiere.

Rezultatul este o **estimare**:

- se numără doar fișierele `.py`, `.xml`, `.js`, `.css` și `.scss`;
- se numără doar liniile nevide (comentariile și docstring-urile intră în total);
- folderele `tests` sunt excluse;
- fișierele care nu pot fi citite ca UTF-8 sunt sărite.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale. Contextul este operațional: dimensionarea efortului
de migrare (de exemplu 19.0 → 20.0) sau de mentenanță, comparația între module, inventarul
personalizărilor unui client.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Administrator (grupul **Setări** / *Administration: Settings*) | Deschide asistentul, alege modulele, citește rezultatul |
| Consultant tehnic | Folosește cifrele în estimări și rapoarte de audit |

Asistentul este accesibil doar utilizatorilor cu drept de administrare a setărilor
(`base.group_system`). Pentru testare: utilizatorul **Administrator**.

## 4. Conturi și date implicate

Nu se folosesc conturi contabile și nu se creează date permanente: asistentul este temporar, iar
rezultatul nu se salvează. Pentru demo sunt suficiente câteva module instalate (de exemplu
`sale`, `deltatech_line_counter` și un modul personalizat al clientului).

## 5. Configurare inițială

1. Instalați modulul `deltatech_line_counter` (depinde doar de `base`).
2. Autentificați-vă cu un utilizator administrator.

Nu există alte setări.

## 6. Flux de utilizare

### Pasul 1 — Deschiderea asistentului

Din meniul **Setări → Numărător linii** (*Settings → Line Counter*) se deschide fereastra
**Numărător linii**, cu câmpul **Module** și butoanele **Numără liniile** (*Count Lines*) și
**Anulează** (*Cancel*).

### Pasul 2 — Alegerea modulelor

În câmpul **Module** adăugați modulele de numărat. Lista propune doar modulele **instalate**; nu se
pot crea module noi din acest câmp. Se pot alege oricâte module.

### Pasul 3 — Numărarea și citirea rezultatului

Apăsați **Numără liniile**. Fereastra rămâne deschisă și afișează sub câmpul **Module** tabelul
**Rezultat**:

1. **Găsiți pe ecran** — fiecare rând are coloana `Module`, cu numele modulului și numele tehnic între
   paranteze (de exemplu `Sales (sale)`), și coloana `Lines`, cu numărul de linii nevide; ultimul rând,
   `Total`, adună toate modulele alese.
2. **Verificați** — fiecare modul ales apare o singură dată; totalul este suma rândurilor; un modul
   fără cod propriu (doar date sau traduceri) poate avea un număr mic, dar nu lipsește din tabel.
   Un modul al cărui folder nu este găsit pe server nu apare în tabel.
3. **Mai departe** — rezultatul nu se salvează și nu are export: copiați tabelul în documentul de
   estimare sau de audit înainte de a închide fereastra. Puteți schimba lista de module și apăsa din
   nou **Numără liniile**; tabelul se recalculează.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr) și nu are rapoarte tipăribile.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `base` | Lista modulelor instalate (`ir.module.module`) și meniul **Setări** |

**Ce e automat:** parcurgerea folderelor modulelor, filtrarea tipurilor de fișiere, excluderea
testelor, totalul.

**Ce rămâne manual:** alegerea modulelor, interpretarea cifrelor (liniile de comentariu intră în
total), copierea rezultatului în documentul de lucru.

## 8. Verificări pentru consultant

- [ ] Meniul **Setări → Numărător linii** apare pentru administrator și lipsește pentru un utilizator
  fără drepturi de administrare.
- [ ] Câmpul **Module** propune doar modulele instalate.
- [ ] După **Numără liniile**, tabelul are câte un rând pentru fiecare modul ales și rândul `Total`.
- [ ] `Total` este egal cu suma coloanei `Lines`.
- [ ] Un modul cu teste nu își numără folderul `tests` (comparați cu numărarea manuală pe server,
  dacă e nevoie).
- [ ] Schimbarea listei și o nouă apăsare pe **Numără liniile** înlocuiesc tabelul.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Meniul **Numărător linii** nu apare | Utilizatorul nu are dreptul de administrare a setărilor | Folosiți un utilizator administrator |
| Un modul ales lipsește din tabel | Folderul modulului nu este găsit pe server (modul instalat, dar scos din `addons_path`) | Verificați `addons_path` sau alegeți alt modul |
| Număr de linii mai mic decât cel așteptat | Fișiere de alt tip (`.scss` e inclus, dar nu `.json`, `.po`, `.md`), fișiere ne-UTF-8 sau teste, toate excluse | Interpretați cifra ca estimare a codului sursă |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`. Dacă e
nevoie de capturi, se pot genera ulterior cu skill-ul `fisa-screenshots`, pentru cei trei pași din
secțiunea 6 (fereastra goală, modulele alese, tabelul **Rezultat**).

## 11. Observații pentru manual

- Rezultatul este o estimare a mărimii codului, nu o măsură a calității sau a complexității.
- Cifrele includ comentariile; pentru comparații între module, folosiți aceeași metodă pe toate.
- Antetele tabelului (`Module`, `Lines`, `Total`) sunt fixe în engleză, indiferent de limba
  utilizatorului.
