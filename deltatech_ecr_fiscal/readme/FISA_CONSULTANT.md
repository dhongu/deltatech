# Fișă Modul: Câmpurile rezultatului de pe casa de marcat (bon fiscal, raport Z, bon simulat)

**Modul:** `deltatech_ecr_fiscal`
**Utilizator principal:** Consultantul care configurează casa de marcat sau modulele de conformitate fiscală
**Prioritate:** 🟢 Scăzută (modul tehnic, fără ecrane proprii; se instalează automat ca dependență)

---

## 1. Scop business

Modulul definește, într-un singur loc, câmpurile în care se păstrează rezultatul tipăririi unui bon pe
casa de marcat fiscală (AMEF): numărul bonului, numărul documentului fiscal, raportul Z, starea, eroarea
și dacă bonul a fost emis de o casă de marcat simulată.

Câmpurile se adaugă pe **facturi și note contabile** (`account.move`) de acest modul și pe **comenzile
POS** de modulele `deltatech_pos` și `l10n_ro_pos_fiscal_compliance_ecr`. Modulul nu are meniu, ecrane sau setări: consultantul îl întâlnește
ca dependență a modulelor de casă de marcat și a celor de conformitate fiscală. Separarea lui permite
modulelor care doar **citesc** numărul bonului (rapoarte, conformitate, localizarea românească) să nu
depindă de modulele care comandă casa de marcat.

## 2. Bază legală și context

Câmpurile nu generează obligații fiscale prin ele însele; ele păstrează în Odoo urma bonului emis de
aparatul de marcat electronic fiscal, pe care o folosesc modulele de conformitate (raportul Z,
jurnalul AMEF). Regulile legale privind aparatele de marcat sunt tratate în acele module, nu aici.

Context pentru consultant:

- aparatul întoarce **două numere**: numărul bonului din raportul Z curent (**BF**), care reîncepe la
  fiecare raport Z, și numărul documentului fiscal (**NR**), unic pe aparat. Când un bon trebuie
  identificat fără ambiguitate (de exemplu la o reclamație sau la o stornare), se folosește **NR**;
- un **bon simulat** nu este document fiscal. Apare când casa de marcat este simulată: emulatorul din
  Odoo sau Terrabit Connect pornit în mod simulat (stația are panglica **Simulare**, vezi fișa
  `deltatech_tc`). Câmpul este pregătit pentru modulele de conformitate, ca acestea să lase bonurile
  simulate în afara raportului Z și a jurnalului AMEF. **În versiunea curentă nici driverele de casă de
  marcat nu îl completează, nici modulele de conformitate nu îl folosesc încă**: un bon simulat nu se
  deosebește deocamdată de unul real prin acest câmp.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Casier / operator de magazin | Tipărește bonul din POS sau din factură; câmpurile se completează automat din răspunsul casei de marcat |
| Contabil | Citește numărul bonului și raportul Z pe document, unde modulul de casă de marcat le afișează |
| Consultant | Verifică, la implementare, că pe baza de producție nu rulează nicio casă de marcat simulată |

Modulul nu adaugă grupuri de drepturi. Câmpurile sunt doar în citire în interfață: nu le modifică
nimeni manual.

## 4. Conturi și date implicate

Nu se folosesc conturi contabile și nu se generează note contabile. Câmpurile adăugate pe documente:

| Câmp (eticheta din interfață) | Nume tehnic | Ce conține | Cine îl scrie |
|---|---|---|---|
| **Fiscal receipt (BF)** | `fiscal_receipt_number` | Numărul bonului în raportul Z curent; reîncepe la fiecare Z | Driverul casei de marcat, după răspunsul aparatului |
| **Fiscal document (NR)** | `fiscal_doc_number` | Numărul documentului fiscal, unic pe aparat | Driverul casei de marcat |
| **Z report** | `fiscal_z` | Numărul raportului Z din care face parte bonul | Driverul casei de marcat |
| **Fiscal state** | `fiscal_state` | Rezultatul tipăririi, așa cum îl raportează driverul (de exemplu `done`, `error`, `canceled`) | Driverul casei de marcat |
| **Fiscal error** | `fiscal_error` | Mesajul de eroare, când aparatul a refuzat sau a eșuat | Driverul casei de marcat |
| **Simulated receipt** | `fiscal_simulated` | Bifat când bonul a fost „tipărit” pe o casă de marcat simulată; bonul nu este document fiscal | Încă niciun driver (câmp pregătit pentru driverele de casă de marcat) |

„Driverul casei de marcat” înseamnă ecranul de plată din POS (`deltatech_pos`) sau acțiunea de
tipărire a bonului din factură (`deltatech_sale_store`), după răspunsul agentului Terrabit Connect.
Câmpurile nu se copiază la duplicarea documentului.

## 5. Configurare inițială

Nu există configurare. Modulul se instalează automat cu modulele care îl folosesc; depinde doar de
`account`. La instalare preia câmpurile definite anterior de `deltatech_pos` și `deltatech_sale_store`,
fără să piardă numerele de bon deja înregistrate.

## 6. Flux de utilizare

Modulul nu are flux propriu de utilizare și **nu are capturi de ecran**: niciun ecran din dependențele
lui (`account`) nu afișează aceste câmpuri. Pe factură, ele apar doar când este instalat modulul de
tipărire a bonului din factură (`deltatech_sale_store`); captura ține de fișa acelui modul. Pe comanda
POS, `deltatech_pos` completează câmpurile, dar nu le afișează: acolo se văd doar prin export.

### Pasul 1 — Unde apar câmpurile pe documente

După tipărirea bonului, modulul de casă de marcat afișează pe document, doar dacă au valoare, starea,
numerele BF și NR, raportul Z și eventuala eroare. Pentru a vedea toate câmpurile, inclusiv **Simulated
receipt**, pe orice factură, exportați facturile din listă (selectați-le, apoi **Acțiuni → Export**)
și alegeți câmpurile de mai sus din lista câmpurilor disponibile.

### Pasul 2 — Ce înseamnă „Simulated receipt” (bon simulat)

Câmpul **Simulated receipt** marchează bonurile emise prin casa de marcat simulată. Driverele de casă de
marcat nu îl completează încă, deci în versiunea curentă rămâne nebifat și pe bonurile simulate. Un
bon simulat:

- **nu** este bon fiscal și nu apare pe aparatul real;
- poate avea BF, NR și Z completate de simulator, ca un bon real; acestea nu corespund unui raport Z
  real;
- trebuie lăsat în afara raportului Z și a jurnalului AMEF; modulele de conformitate nu fac încă
  această excludere pe baza câmpului, deci până atunci casa de marcat simulată nu se folosește pe o
  bază de producție.

Pentru a verifica dacă o casă de marcat este simulată, aveți două locuri:

- stațiile Terrabit Connect din **Setări → Terrabit Connect → Stații**: stația cu panglica
  **Simulare** rulează în mod simulat;
- câmpul **Simulation** din setările casei de marcat ale punctului de vânzare (**Punct de vânzare →
  Configurare → Setări**, blocul casei de marcat, vizibil doar cu transportul Terrabit Connect; modulul
  `deltatech_pos_base`): simularea „în Odoo” nu trece prin Terrabit Connect, deci stația nu arată
  panglica.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr) și nu are rapoarte. Raportul Z și jurnalul AMEF sunt în
modulele de conformitate fiscală, care citesc aceste câmpuri.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `account` | Singura dependență; câmpurile se adaugă pe `account.move` |
| `deltatech_pos` | Aplică aceleași câmpuri pe comenzile POS și le completează din ecranul de plată |
| `l10n_ro_pos_fiscal_compliance_ecr` (`l10n_ro_ent`) | Aplică mixinul pe comenzile POS și potrivește bonurile cu jurnalul AMEF după Z și BF |
| `deltatech_sale_store` | Tipărește bonul din factură și afișează câmpurile pe formularul facturii |
| `deltatech_tc` | Stațiile Terrabit Connect; arată dacă o stație simulează casa de marcat |
| `l10n_ro_pos_fiscal_compliance` (`l10n_ro_ent`) | Stările bonurilor POS și jurnalul AMEF, pe care le leagă de comenzi prin modulul `_ecr` |

**Ce e automat:** completarea câmpurilor BF, NR, Z, stare și eroare după fiecare bon, preluarea
câmpurilor de la modulele vechi la instalare.

**Ce rămâne manual:** verificarea că nicio casă de marcat nu e simulată pe baza de producție
(stațiile din `deltatech_tc` și setarea de simulare a punctului de vânzare).

## 8. Verificări pentru consultant

- [ ] Pe o factură cu bon tipărit (cu `deltatech_sale_store`), apar starea, BF, NR și Z.
- [ ] Exportul facturilor (**Acțiuni → Export**) oferă câmpul **Simulated receipt** și îl arată
  nebifat (niciun driver nu îl completează încă).
- [ ] Pe baza de producție, nicio stație din **Setări → Terrabit Connect → Stații** nu are panglica
  **Simulare**.
- [ ] Pe baza de producție, niciun punct de vânzare nu are setat câmpul **Simulation** al casei de
  marcat.
- [ ] La duplicarea unei facturi cu bon, câmpurile fiscale nu se copiază.
- [ ] După actualizarea `deltatech_pos` sau `deltatech_sale_store`, numerele de bon vechi sunt încă pe
  documente.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| **Fiscal error** completat, **Fiscal state** = `error` | Casa de marcat a refuzat bonul (hârtie, raport Z neînchis, aparat oprit) | Rezolvați cauza pe aparat și tipăriți din nou bonul din modulul de casă de marcat |
| Câmpurile nu apar pe factură | Nu este instalat modulul care le afișează | Instalați modulul de tipărire a bonului (`deltatech_sale_store`) sau exportați facturile (**Acțiuni → Export**) |
| Bonuri emise pe casa simulată pe baza de producție | O stație Terrabit Connect a rămas în mod simulat sau punctul de vânzare are simularea activă | Opriți simularea în Terrabit Connect (verificați stația în **Setări → Terrabit Connect → Stații**) și în configurarea punctului de vânzare |

## 10. Capturi de ecran

Modulul **nu are capturi de ecran** și nici `tests/test_screenshots.py`. Câmpurile sunt moștenite de
factură (`account.move`), dar niciun ecran din dependențele minime ale modulului (`account`) nu le
afișează, iar modulul nu adaugă view-uri. O captură ar arăta doar formularul standard al facturii,
fără câmpurile fiscale. Câmpurile se văd pe ecran în fișa modulului care le afișează
(`deltatech_sale_store`), iar marcajul de simulare al stației în fișa `deltatech_tc`.

## 11. Observații pentru manual

- Etichetele câmpurilor nu sunt traduse în română (**Fiscal receipt (BF)**, **Simulated receipt**...).
- Pentru identificarea unui bon folosiți **NR**, nu **BF**: BF se repetă după fiecare raport Z.
- Un bon simulat nu este document fiscal, chiar dacă are numere completate.
- **Simulated receipt** este nou în versiunea 19.0.1.0.4 și deocamdată doar pregătit: niciun driver
  nu îl completează și niciun modul de conformitate nu îl citește. Actualizați fișa când driverele îl
  vor scrie.
- Modulul nu se instalează separat: vine cu modulele de casă de marcat.
