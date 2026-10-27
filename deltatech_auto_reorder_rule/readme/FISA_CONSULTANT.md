# Fișă Modul: Reguli de reaprovizionare create automat

**Modul:** `deltatech_auto_reorder_rule`
**Utilizator principal:** Responsabil stocuri / achiziții (configurarea o face consultantul)
**Prioritate:** 🟡 Medie (scutește munca manuală la cataloage mari, dar nu are efect contabil)

---

## 1. Scop business

În Odoo, un produs intră în calculul de reaprovizionare doar dacă are o **regulă de reaprovizionare**
(min/max) pe locația de stoc. Într-o firmă cu mii de articole, crearea manuală a acestor reguli este
lentă și se uită ușor la produsele noi. Modulul creează automat câte o regulă pentru fiecare produs nou,
în fiecare depozit care are opțiunea activată, și oferă două acțiuni pentru produsele existente:
completarea în masă a regulilor lipsă și un asistent pentru reguli cu cantități proprii.

Pe versiunea 19.0, regulile se creează pentru **orice produs nou**, indiferent dacă are bifa *Track
Inventory* (produs stocabil) sau nu. Un produs care primește regulă nu mai poate avea o listă de
materiale de tip kit (Odoo o refuză); pentru produsele kit sau nestocate, regula trebuie ștearsă înainte
(vezi secțiunea 9). Filtrarea pe produse stocabile există doar de la versiunea 20.0 a modulului.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale. Contextul este operațional: planificarea
aprovizionării pe baza stocului minim și maxim. Regulile create automat au minimul și maximul **0** și
declanșarea **manuală**, deci nu generează singure cereri de ofertă; ele fac produsul vizibil în ecranul
de reaprovizionare, unde responsabilul completează cantitățile.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Consultant / administrator stocuri | Activează opțiunea pe depozite, marchează ruta pentru regulile automate, setează parametrul de sistem dacă e cazul |
| Responsabil stocuri / achiziții | Creează produse noi, rulează acțiunile **Create rule** și **Open Rules Wizard**, completează min/max în ecranul de reaprovizionare |

Roluri recomandate pentru testare: **Inventory / Administrator** (configurarea depozitelor și rutelor) și
un utilizator cu drept de creare a produselor. Asistentul este accesibil oricărui utilizator intern.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile și nu generează note contabile.

Date minime pentru demo:

- două depozite, ca să se vadă o regulă pe fiecare (și, pentru completarea în masă, un depozit activat
  ulterior);
- o rută de aprovizionare (de exemplu *Buy*) marcată pentru regulile automate;
- un produs stocabil nou;
- un produs existent fără regulă, pentru acțiunea în masă.

## 5. Configurare inițială

1. Instalați modulul `deltatech_auto_reorder_rule` (depinde de `stock`, `purchase_stock`, `sale_stock`).
2. **Inventory → Configuration → Warehouses**, deschideți fiecare depozit și bifați **Generate Reorder
   Rules** (este bifat implicit la depozitele noi). Câmpul apare în secțiunea **Resupply**, vizibilă doar
   când sunt activate depozitele multiple sau locațiile multiple (**Inventory → Configuration →
   Settings**).
3. **Inventory → Configuration → Routes**, deschideți ruta dorită (de exemplu *Buy*) și bifați **Use This
   for Auto Rules**, în zona în care se alege unde se aplică ruta (lângă **Sales Order Lines**). Marcați o
   singură rută; fără rută marcată, regulile se creează fără rută.
4. Opțional, pentru a opri crearea automată la salvarea produsului fără a dezinstala modulul:
   **Settings → Technical → System Parameters**, cheia `deltatech_auto_reorder_rule.dont_auto_create_rule`
   cu valoarea `True` (sau `1`, `yes`). Orice altă valoare, inclusiv `False`, lasă crearea automată
   pornită. Acțiunile manuale rămân disponibile.

## 6. Flux de utilizare

### Pasul 1 — Crearea automată la un produs nou

**Inventory → Products → Products → New**. Completați produsul și salvați.

Ce se întâmplă: pentru fiecare depozit cu **Generate Reorder Rules**, al companiei produsului (sau al
companiei active, la produsele comune mai multor companii), se creează o regulă pe locația de stoc a
depozitului, cu **Min** 0, **Max** 0, declanșare **Manual** și ruta marcată **Use This for Auto Rules**.
Regula se creează indiferent de tipul produsului.

### Pasul 2 — Completarea în masă a regulilor lipsă

**Inventory → Products → Products**, în vizualizarea listă selectați produsele, apoi **Actions → Create
rule**. Acțiunea este disponibilă și din formularul produsului (meniul **Actions**).

Ce se întâmplă: fiecare depozit activat este verificat separat. Pentru fiecare variantă a produselor
selectate se creează regula doar în depozitele în care lipsește; regulile existente (inclusiv cele
arhivate) se păstrează și nu se dublează. Astfel, un depozit activat ulterior primește regulile lui, chiar
dacă produsele au deja reguli în alte depozite.

### Pasul 3 — Reguli cu cantități proprii (asistent)

Deschideți formularul unui produs (**Inventory → Products → Products**, apoi produsul) și alegeți
**Actions → Open Rules Wizard**. În fereastra **Order Rules Details** completați:

- **Minimum Quantity** — nivelul de stoc sub care se declanșează reaprovizionarea;
- **Maximum Quantity** — nivelul până la care se reaprovizionează;
- **Trigger** — *Automatic* (planificatorul generează singur comenzile) sau *Manual*;
- **Stock Locations** — una sau mai multe locații pentru care se creează reguli.

Apăsați **Create Rules**. Se creează câte o regulă pentru fiecare variantă a produsului și fiecare
locație aleasă. Fiecare regulă primește compania locației ei (sau compania activă, pentru locațiile fără
companie) și ruta marcată pentru regulile automate a acelei companii (sau o rută fără companie).
Asistentul nu verifică dacă există deja o regulă: folosiți-l pe locații fără regulă, ca să nu apară
reguli duble.

### Pasul 4 — Verificarea regulilor create

**Inventory → Operations → Replenishment**. Găsiți pe ecran produsele noi: fiecare apare cu câte un rând
pe locația de stoc a fiecărui depozit activat, cu **Min** și **Max** 0 și **Trigger** *Manual* (sau
valorile din asistent). Verificați că ruta afișată este cea marcată la configurare și că fiecare depozit
activat are exact o regulă pe produs. Abia apoi completați cantitățile minime și maxime reale, direct în
listă.

### Note de monografie și raportare

Nu se generează note contabile (Dr/Cr). Regulile influențează doar propunerile de aprovizionare
(cereri de ofertă, ordine de producție sau transferuri), care urmează fluxul standard Odoo.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `stock` | regulile de reaprovizionare, depozitele și ecranul **Replenishment** |
| `purchase_stock` | secțiunea **Resupply** din depozit, ruta *Buy* |
| `sale_stock` | zona din formularul rutei unde se află bifa **Use This for Auto Rules** |
| `mrp` (dacă e instalat) | interzice o listă de materiale de tip kit pentru un produs cu regulă |

**Ce e automat:** crearea regulii la salvarea unui produs nou, pe compania corectă, în fiecare depozit
activat, cu ruta marcată; completarea regulilor lipsă pe depozit, fără dubluri.

**Ce rămâne manual:** completarea cantităților minime/maxime reale, trecerea declanșării pe *Automatic*,
ștergerea regulilor pentru produsele kit sau nestocate, crearea regulilor pentru locații suplimentare
(asistentul).

## 8. Verificări pentru consultant

- [ ] Un produs nou primește câte o regulă în fiecare depozit cu **Generate Reorder Rules** și niciuna
  în depozitele fără bifă.
- [ ] Regula automată are **Min** 0, **Max** 0, **Trigger** *Manual* și ruta marcată **Use This for Auto
  Rules**.
- [ ] Într-un mediu cu mai multe companii, un produs creat în compania activă primește regula pe
  depozitul acelei companii.
- [ ] După activarea **Generate Reorder Rules** pe un depozit nou, **Actions → Create rule** creează
  regulile doar în acel depozit; rularea a doua oară nu dublează regulile.
- [ ] **Open Rules Wizard** cu o locație a altei companii permise creează regula în compania locației,
  fără eroare.
- [ ] Cu parametrul `deltatech_auto_reorder_rule.dont_auto_create_rule` = `True`, produsul nou nu mai
  primește regulă, dar **Create rule** funcționează; cu `False`, regula se creează.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `You can not create a kit-type bill of materials for products that have at least one reordering rule.` | Produsul a primit automat o regulă la creare (pe 19.0 se creează pentru orice produs) | Ștergeți regulile produsului din **Replenishment** înainte de a crea lista de tip kit |
| `The minimum quantity must be less than or equal to the maximum quantity.` | În asistent, **Minimum Quantity** e mai mare decât **Maximum Quantity** | Corectați cantitățile |
| Produsul nou nu are regulă | Depozitul nu are **Generate Reorder Rules** sau parametrul de sistem oprește crearea | Verificați depozitul și parametrul |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița, bannerul și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`.
Dacă se doresc capturi, ele se generează cu skill-ul `fisa-screenshots` (formularul depozitului,
formularul rutei, acțiunea **Create rule**, asistentul **Order Rules Details**, ecranul
**Replenishment**) și se leagă apoi în pașii din secțiunea 6.

## 11. Observații pentru manual

- Pe 19.0, regula se creează pentru orice produs nou; manualul trebuie să avertizeze că produsele kit
  au nevoie de ștergerea regulii înainte de lista de materiale.
- Bifa **Generate Reorder Rules** se vede doar cu depozite multiple sau locații multiple activate; merită
  menționat, altfel utilizatorul nu o găsește.
- Regulile automate sunt doar un punct de plecare (min/max 0, manual); manualul trebuie să spună clar că
  aprovizionarea nu pornește până nu se completează cantitățile.
