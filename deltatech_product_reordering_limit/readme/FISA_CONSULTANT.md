# Fișă Modul: Stoc minim și maxim pe produs, cu raport de reaprovizionare

**Modul:** `deltatech_product_reordering_limit`
**Utilizator principal:** Responsabil de aprovizionare / gestionar (urmărește produsele sub stocul
minim și comandă), responsabil de nomenclator (stabilește limitele)
**Prioritate:** 🟡 Medie (sprijină aprovizionarea zilnică, fără efect contabil)

---

## 1. Scop business

Multe firme vor o regulă simplă de aprovizionare: „din hârtia A4 trebuie să avem mereu cel puțin
50 de topuri și să nu depășim 200”. Regulile de reaprovizionare din Odoo standard se definesc pe
depozit și locație și generează singure cereri de achiziție, ceea ce e prea mult pentru o firmă cu
un singur stoc sau care vrea doar să **vadă** ce trebuie comandat. Modulul adaugă pe produs un
**Total Minimum** și un **Total Maximum**, valabile pentru tot stocul produsului, un filtru
**Below Minimum** care arată produsele sub minim și un **raport Excel** cu cantitatea lipsă până la
minim și cea necesară până la maxim. Decizia de comandă rămâne la om.

## 2. Bază legală și context

- Modulul **nu are efect fiscal sau contabil**: nu creează comenzi, nu modifică stocul și nu
  generează note contabile.
- Limitele sunt un instrument de **gestiune internă** a stocurilor. Ele nu înlocuiesc regulile de
  reaprovizionare standard (**Inventar → Configurare → Reguli reaprovizionare**) și nu
  interacționează cu ele.

## 3. Utilizatori și roluri

| Rol | Ce poate face |
|---|---|
| **Produse: Creează** (în **Date de bază**) | completează **Total Minimum** și **Total Maximum** pe produs |
| Orice utilizator intern | folosește filtrul **Below Minimum** și generează raportul Excel |

Roluri recomandate pentru testare:
- un **responsabil de nomenclator**, care stabilește limitele;
- un **gestionar** (Inventar: Utilizator), care caută produsele sub minim și descarcă raportul.

## 4. Conturi și date implicate

Modulul **nu generează note contabile** și nu atinge conturi. Date minime pentru demo (toate de tip
**Bunuri**, urmărite în stoc, într-un singur depozit):

| Produs | Referință internă | Stoc disponibil | Total Minimum | Total Maximum |
|---|---|---|---|---|
| Hârtie copiator A4 (top) | HRT-A4 | 30 | 50 | 200 |
| Toner imprimantă laser | TNR-01 | 8 | 5 | 15 |
| Capsator de birou | CPS-01 | 12 | 0 | 0 |

## 5. Configurare inițială

1. Instalați `deltatech_product_reordering_limit` (dependențe: `product`, `stock`; biblioteca Python
   `xlsxwriter`, prezentă de regulă într-o instalare Odoo).
2. Stabiliți cu clientul pentru ce produse are sens un stoc minim. Produsele cu **Total Minimum** 0
   nu apar niciodată ca „sub minim”.
3. Limitele sunt în **unitatea de măsură a produsului** (de exemplu bucăți, topuri, kg) și se compară
   cu stocul din toate locațiile interne, cumulat pe toate variantele produsului.

## 6. Flux de utilizare

### Pasul 1 — Stabilirea limitelor pe produs

Deschideți produsul din **Inventar → Produse → Produse** (de exemplu „Hârtie copiator A4 (top)”). În
fila **Informații generale**, la sfârșitul primei coloane (cea care începe cu **Tip produs**),
completați:

- **Total Minimum** — stocul sub care produsul trebuie recomandat (50);
- **Total Maximum** — stocul până la care se comandă (200).

Salvați. Etichetele câmpurilor apar în engleză: modulul nu are încă traducere în română.

### Pasul 2 — Produsele sub stocul minim

Deschideți **Inventar → Produse → Produse**, treceți pe vizualizarea **Listă** (implicit se deschide
**Kanban**) și, din căutare, deschideți meniul de filtre. Sub
filtrele **Vânzări** / **Achiziții** apare filtrul **Below Minimum**. Alegeți-l (și scoateți
celelalte filtre, dacă vreți toate produsele).

**Găsiți pe ecran:** lista conține doar produsele cu stocul disponibil sub **Total Minimum**: în demo,
„Hârtie copiator A4 (top)” (30 < 50).

**Verificați:**
- tonerul nu apare (8 ≥ 5), iar capsatorul nu apare (fără minim);
- coloana **În stoc** a listei arată, pentru fiecare produs găsit, o valoare mai mică decât minimul
  lui.

Filtrul folosește același stoc ca fișa produsului: companiile alese în selectorul de companii și,
dacă lista este deschisă pentru un depozit anume, doar stocul acelui depozit.

### Pasul 3 — Generarea raportului de reaprovizionare

În lista de produse (de exemplu cea filtrată la pasul 2 sau toate produsele cu limite), bifați
produsele dorite, apoi deschideți **Acțiuni** (rotița ⚙ de deasupra listei) și alegeți **Generate
Reordering Report**. Se deschide fereastra **Generate Reordering Report**; apăsați **Generate Excel**.

### Pasul 4 — Descărcarea și citirea raportului

După generare, fereastra arată câmpul **File**, cu fișierul **Reordering_Report.xlsx**. Apăsați pe el
pentru descărcare, apoi **Close**.

Fișierul are o foaie, **Reordering Report**, cu o linie pe produs bifat și coloanele:

| Coloană | Conținut |
|---|---|
| **Default Code** | referința internă |
| **Name** | numele produsului |
| **Under Quantity** | cât lipsește până la minim: minim − stoc disponibil (0 dacă stocul e peste minim), cu roșu când e mai mare ca 0 |
| **Required Quantity** | cât trebuie comandat până la maxim: maxim − stoc disponibil (0 dacă stocul e peste maxim), cu verde când e mai mare ca 0 |
| **Range** | intervalul minim → maxim, de exemplu „50.0 -> 200.0” |

**Verificați** pe exemplul demo:
- hârtia: **Under Quantity** 20 (50 − 30), **Required Quantity** 170 (200 − 30);
- tonerul: **Under Quantity** 0, **Required Quantity** 7 (15 − 8);
- capsatorul: ambele 0, interval „0.0 -> 0.0”.

Abia după aceste verificări folosiți **Required Quantity** pentru comenzile de achiziție sau de
producție, pe care le creați manual.

### Note de monografie și raportare

Modulul **nu înregistrează nicio notă contabilă**. Raportul Excel este un instrument de lucru: nu
se păstrează în Odoo după închiderea ferestrei și se generează din nou ori de câte ori e nevoie, cu
stocul de la acel moment.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux |
|---|---|
| `product` | fișa produsului, unde se completează limitele, și lista de produse cu filtrele |
| `stock` | stocul disponibil cu care se compară limitele |
| `purchase` / `mrp` (opțional) | comenzile de achiziție sau de producție create manual pe baza raportului |

Ce este automat: marcarea produselor sub minim (filtrul **Below Minimum**), calculul cantităților
lipsă și necesare din raport.

Ce rămâne manual: stabilirea limitelor, generarea raportului și crearea comenzilor de
reaprovizionare.

## 8. Verificări pentru consultant

- [ ] Fila **Informații generale** a produsului are câmpurile **Total Minimum** și **Total Maximum**.
- [ ] Filtrul **Below Minimum** apare în lista de produse, după **Vânzări** / **Achiziții**.
- [ ] Cu demo-ul, **Below Minimum** arată doar hârtia A4.
- [ ] Un produs cu **Total Minimum** 0 nu apare niciodată în filtru.
- [ ] **Generate Reordering Report** apare în **Acțiuni** după bifarea produselor din listă.
- [ ] Raportul are, pentru hârtie, 20 la **Under Quantity** (cu roșu) și 170 la **Required
      Quantity** (cu verde).
- [ ] Fără produse bifate, acțiunea nu e disponibilă; deschisă altfel, fereastra refuză generarea cu
      mesaj clar.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| „Select at least one product to generate the reordering report.” | Fereastra a fost deschisă fără produse bifate (sau din alt ecran decât lista de produse) | Bifați produsele în **Inventar → Produse → Produse** și porniți din nou acțiunea |
| **Below Minimum** arată alt rezultat decât se aștepta utilizatorul | În selectorul de companii sunt alese alte companii decât cea vizată | Alegeți în selectorul de companii doar compania (sau companiile) pentru care se face aprovizionarea |
| Etichetele câmpurilor și ale raportului sunt în engleză | Modulul nu are traducere în română | Comportament actual; folosiți denumirile din fișă |
| Raportul nu se generează (eroare despre `xlsxwriter`) | Biblioteca Python lipsește de pe server | Instalați `xlsxwriter` pe server |

## 10. Capturi de ecran

Fișa este, deocamdată, **doar text**: nu are capturi de ecran. Capturile planificate, în ordinea
pașilor din secțiunea 6:

1. `01_produs_limite.png` — fila „Informații generale” cu „Total Minimum” și „Total Maximum”.
2. `02_filtru_below_minimum.png` — lista de produse cu filtrul „Below Minimum”.
3. `03_actiune_raport.png` — meniul „Acțiuni” cu „Generate Reordering Report” și fereastra de generare.
4. `04_raport_descarcare.png` — fereastra cu fișierul „Reordering_Report.xlsx”.
5. `05_raport_xlsx.png` — conținutul raportului Excel pentru produsele din demo.

Ele se pot genera ulterior cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`; captura 5 cu helperul `xlsx_shot`), în limba
română, după care se leagă în pașii din secțiunea 6.

## 11. Observații pentru manual

Prezentați modulul ca o alternativă **simplă** la regulile de reaprovizionare: limitele se pun pe
produs, iar Odoo doar arată ce e sub minim și cât trebuie comandat; comenzile le face omul. Explicați
diferența dintre cele două coloane ale raportului (**Under Quantity** = urgent, până la minim;
**Required Quantity** = cât să comandați, până la maxim). La clienții cu mai multe companii, arătați
că filtrul și raportul folosesc stocul companiilor alese în selectorul de companii.
