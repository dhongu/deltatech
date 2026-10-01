# Fișă Modul: Decont de cheltuieli din avans de trezorerie (542) și diurnă

**Modul:** `deltatech_expenses`
**Utilizator principal:** Contabil, Casier, Operator deconturi
**Prioritate:** 🔴 Ridicată (flux frecvent în practica românească)

---

## 1. Scop business

Modulul gestionează **decontul de cheltuieli al angajatului pornind de la un avans de trezorerie**
(cont 542), specific contabilității din România. Angajatul primește un avans, efectuează cheltuieli
(cazare, transport, protocol etc.) și, eventual, beneficiază de diurnă; la final, decontul calculează
automat diferența de restituit sau de încasat și generează notele contabile, inclusiv chitanțele de
achiziție și plățile, închizând soldul contului 542 al angajatului.

## 2. Bază legală și context

- Ordinul 2634/2015 — documentul „Decont de cheltuieli" și „Ordin de deplasare (delegație)".
- Reglementări privind diurna internă/externă pentru deplasări.
- Plan de conturi conform OMFP 1802/2014: 542 „Avansuri de trezorerie", 625 „Cheltuieli cu
  deplasări, detașări și transferări", 4426 „TVA deductibilă".

## 3. Utilizatori și roluri

Contabil, Casier, Operator deconturi.

Roluri recomandate pentru testare:
- Administrator funcțional: instalează modulul, configurează jurnalele și contul de avans.
- Operator: introduce decontul, avansul și liniile de cheltuieli.
- Contabil/manager: validează notele contabile și închiderea contului 542.

## 4. Conturi și date implicate

- **542** — Avansuri de trezorerie (contul angajatului care se închide la final).
- **5311 / 5121** — Casa / Bancă (sursa avansului).
- **625 / 623** — Cheltuieli cu deplasări / de protocol.
- **4426** — TVA deductibilă aferentă cheltuielilor.

Date minime pentru demo:
- companie românească cu localizarea contabilă instalată (RON);
- un angajat `hr.employee` cu „Work Contact" completat (partenerul folosit pe notele contabile);
- jurnal de numerar (Casă), un jurnal general cu **contul implicit = 542** (pentru avans/decont) și
  un jurnal pentru diurnă.

## 5. Configurare inițială

1. Instalați modulul `deltatech_expenses` (atrage și `hr`). Dacă folosiți și modulul standard de
   cheltuieli (`hr_expense`), instalați și `deltatech_expenses_hr_expense` pentru puntea de preluare
   a cheltuielilor standard în decont (vezi fișa acelui modul).
2. Creați/identificați un jurnal general al cărui **cont implicit este 542** și folosiți-l ca
   „Jurnal cheltuieli" pe decont.
3. Verificați jurnalul de numerar (Casă) și contul său implicit (5311).
4. Configurați contul de diurnă (625) și jurnalul de diurnă.
5. Asigurați-vă că angajații au „Work Contact" completat (sau lăsați-l gol pentru note interne, fără
   partener).

## 6. Flux de utilizare

### Pasul 1 — Crearea decontului și acordarea avansului

Accesați decontul de cheltuieli, alegeți **angajatul**, **jurnalul de numerar** și **jurnalul de
cheltuieli** (cu contul 542), completați **avansul** acordat și, dacă e cazul, **diurna** (sumă/zi și
numărul de zile). La **Avans** documentul trece în starea „Avans"; pe măsură ce adăugați liniile de
cheltuieli, se calculează automat totalul și **diferența** față de avans.

![Decontul în starea „Avans": avans, linii de cheltuieli, diurnă și diferență](screenshots/01_decont_avans.png)

Acordarea avansului generează nota contabilă **Dr 542 = Cr 5311** (avansul iese din casă în contul de
avansuri de trezorerie al angajatului).

![Nota contabilă de acordare a avansului (542 = 5311)](screenshots/02_nota_avans.png)

> **Preluare din modulul standard de cheltuieli:** dacă instalați și `deltatech_expenses_hr_expense`,
> pe formularul decontului apare butonul **„Preia cheltuieli HR"**, care preia cheltuielile eligibile
> din `hr.expense` ca linii de decont. Detaliile acelui flux sunt descrise în fișa modulului-punte.

### Pasul 2 — Introducerea cheltuielilor și validarea decontului

Adăugați liniile de cheltuieli (furnizor, sumă cu TVA inclus, cont de cheltuială). Fiecare linie are
un **tip**:

- **Cheltuieli** — justificată cu bon/factură; la validare se generează o **chitanță de achiziție** și
  decontarea din avans (vezi mai jos);
- **Plată furnizor** — angajatul a achitat direct o datorie a firmei către un furnizor (fără chitanță
  proprie); la validare se generează doar nota `Dr 401 = Cr 542`, care se **reconciliază cu facturile
  furnizor deschise** ale aceluiași furnizor (stinge datoria, ca o plată). Dacă furnizorul nu are
  datorii deschise, suma rămâne ca avans către furnizor.

La **Validează**, decontul trece în starea „Efectuat": modulul generează chitanțele de achiziție,
notele de decontare din avans, nota de diurnă și nota de diferență, închizând soldul contului 542.

![Decontul validat (starea „Efectuat")](screenshots/06_decont_validat.png)

Pentru fiecare cheltuială se generează o **notă de decontare din avans** care stinge datoria către
furnizor pe seama avansului: **Dr 401 (Furnizori) = Cr 542 (Avansuri de trezorerie)**, reconciliată cu
chitanța de achiziție.

![Nota de decontare din avans (Dr 401 = Cr 542)](screenshots/07_nota_decontare.png)

### Note de monografie și raportare (notele generate la fiecare pas)

- **Acordare avans** (Pasul 1): **Dr 542 = Cr 5311/5121** (suma avansului);
- **Decontare cheltuieli** (Pasul 2, la validare), pentru liniile de tip „Cheltuieli", în două note:
  - chitanța de achiziție: **Dr 6xx + Dr 4426 = Cr 401** (cheltuială fără TVA + TVA deductibil);
  - decontarea din avans: **Dr 401 = Cr 542** (reconciliată cu chitanța);
- **Plată furnizor** (Pasul 2, liniile de tip „Plată furnizor"): **Dr 401 = Cr 542**, reconciliată cu
  facturile furnizor deschise;
- **Diurnă** (la validare): **Dr 625 = Cr 542** (totalul diurnei);
- **Diferență** (la validare): **Dr/Cr 5311 = Cr/Dr 542**, astfel încât soldul 542 al angajatului
  devine **zero**.

### Pasul 3 — Urmărirea deconturilor pe angajat

Fișa angajatului afișează butonul smart **„Deconturi"** cu numărul deconturilor; un clic deschide
lista filtrată pentru acel angajat.

![Fișa angajatului cu butonul smart „Deconturi"](screenshots/05_angajat_deconturi.png)

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux |
|---|---|
| `account` | note contabile de avans, decontare, diurnă și diferență; chitanțe `in_receipt` și plăți |
| `hr` | angajatul (`hr.employee`); partenerul contabil derivă din `work_contact_id` |
| `deltatech_expenses_hr_expense` (opțional) | preluarea cheltuielilor standard `hr_expense` în decont și prevenirea dublei contabilizări |
| `l10n_ro` | planul de conturi și TVA-ul românesc |
| `deltatech_partner_generic` | partener generic pentru liniile fără furnizor explicit |

Ce este automat: generarea notelor contabile, calculul diferenței și al diurnei, închiderea contului 542.
Ce rămâne manual: configurarea jurnalelor/conturilor și verificarea soldului 542 după validare.

## 8. Verificări pentru consultant

- [ ] Modulul se instalează fără erori pe baza demo.
- [ ] Jurnalul de cheltuieli are contul implicit 542.
- [ ] Acordarea avansului produce nota Dr 542 = Cr 5311.
- [ ] Liniile de cheltuieli calculează corect subtotalul și TVA-ul deductibil.
- [ ] Diferența (avans − cheltuieli − diurnă) este corectă.
- [ ] După validare, soldul contului 542 al angajatului este zero.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| Notele de avans nu au partener | Angajatul nu are „Work Contact" | Completați partenerul pe fișa angajatului (sau acceptați note interne) |
| Contul 542 nu se închide | Jurnalul de cheltuieli nu are contul implicit 542 | Setați contul implicit 542 pe jurnalul de cheltuieli |
| „Furnizorul ... nu are un cont de datorii (401)" | Linie „Plată furnizor" cu un furnizor fără cont de plătit configurat | Completați „Cont de plătit" pe fișa furnizorului |

Pentru mesajele legate de preluarea cheltuielilor standard (`hr_expense`), vezi fișa modulului
`deltatech_expenses_hr_expense`.

## 10. Capturi de ecran

Capturile (`readme/screenshots/`) sunt **generate automat** din `tests/test_screenshots.py`
(mixinul `ScreenshotCase` din `l10n_ro_doc_screenshots`, import defensiv), în **limba română**, pe
planul de conturi RO (`setup_country("ro")`):

1. `01_decont_avans.png` — decontul în starea „Avans": avans 1.000 lei, linii de cheltuieli (cazare,
   transport), diurnă (2 zile × 42,50) și diferența calculată.
2. `02_nota_avans.png` — nota contabilă de acordare a avansului (Dr 542 = Cr 5311).
3. `05_angajat_deconturi.png` — fișa angajatului cu butonul smart „Deconturi".
4. `06_decont_validat.png` — decontul în starea „Efectuat" după validare.
5. `07_nota_decontare.png` — nota de decontare din avans (Dr 401 = Cr 542), reconciliată cu chitanța.

Capturile wizard-ului „Preia cheltuieli HR" (fostele `03`/`04`) s-au mutat în modulul
`deltatech_expenses_hr_expense`, care le generează acum independent.

Regenerare:

```bash
./odoo/odoo-bin -c odoo.conf -d <db> -u deltatech_expenses -i l10n_ro_doc_screenshots \
    --test-tags=fise_screenshots --stop-after-init
```

## 11. Observații pentru manual

În manualul final, păstrați explicația orientată pe activitatea utilizatorului: când se acordă avansul,
ce documente justificative se adaugă, cum se citește diferența de restituit/încasat și cum se verifică
închiderea contului 542. Notele contabile se prezintă în detaliu (liniile Dr/Cr), iar integrarea cu
`hr_expense` se menționează ca opțiune pentru companiile care folosesc și fluxul standard de cheltuieli.
