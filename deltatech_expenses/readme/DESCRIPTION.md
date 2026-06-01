Features:

- Introducerea decontului de cheltuieli într-un document distinct care generează automat chitanțe de achiziție
- Validarea documentului duce la generarea notelor contabile de avans și înregistrarea plăților

Configurare:
- În registrul de numerar trebuie completat câmpul "Cash advances" cu 542.
- Angajații sunt înregistrați ca `hr.employee`. Dacă angajatul are completat câmpul "Work Contact"
  (partenerul), acesta este folosit pe notele contabile. Dacă nu, notele se generează fără partener
  (înregistrări interne) — validarea decontului funcționează în ambele cazuri.


# Diferența față de modulul standard `hr_expense`

Acest modul **nu** înlocuiește și **nu** se suprapune cu modulul standard `hr_expense`. Cele două
acoperă procese de business distincte și pot coexista în aceeași bază de date:

| Aspect | `deltatech_expenses` (acest modul) | `hr_expense` (standard Odoo) |
|---|---|---|
| **Scop** | Decont de cheltuieli din **avans de trezorerie** (cont 542), specific contabilității din România | Notă de cheltuială angajat → **rambursare** sumelor plătite din buzunar |
| **Model central** | `deltatech.expenses.deduction` (moștenește doar `mail.thread`) | `hr.expense` / `hr.expense.sheet` |
| **Angajatul** | `hr.employee` (`employee_id`); partenerul contabil derivă din `work_contact_id` | `hr.employee`, flux integrat HR |
| **Avans de trezorerie (542)** | Da — acordare, decontare și închiderea contului 542 | Nu |
| **Diurnă** | Da — câmp `diem` (implicit 42,5) și calcul `total_diem` | Nu |
| **Documente generate** | Chitanțe de achiziție (`in_receipt`), plăți (`account.payment`) și note contabile de diferență/diurnă | În funcție de modul de plată (vezi mai jos) |
| **Dependențe** | `l10n_ro`, `account`, `product`, `hr`, `hr_expense`, `deltatech_partner_generic` | `hr`, `account` |
| **Specific RO** | Da — numerotare proprie, jurnale casă/diurnă, plan de conturi RO | Nu (generic, multi-țară) |

## Notele contabile generate de `hr_expense`

Și `hr_expense` generează note contabile (`account.move`) la postare, dar tipul lor depinde de **modul de plată** al cheltuielii:

- **Plătită de angajat** (`payment_mode = own_account`): se creează un `account.move` de tip chitanță de achiziție
  (`in_receipt`) — debit cont de cheltuială (6xx) + TVA deductibil / credit **contul de datorie (payable) al angajatului**.
  Firma rămâne datoare angajatului, urmând rambursarea efectivă.
- **Plătită de firmă** (`payment_mode = company_account`): se creează direct note de plată legate de un `account.payment` —
  debit cont de cheltuială + TVA / credit cont **bancă/casă**. Nu mai există datorie de rambursat, fiindcă firma a achitat deja.

În ambele cazuri contrapartida este fie **datoria către angajat**, fie **trezoreria firmei** — niciodată un avans de decontat (cont 542),
care este specific modulului `deltatech_expenses`.

Pe scurt: folosește **`deltatech_expenses`** pentru fluxul românesc *avans de trezorerie → decont → diurnă →
închidere cont 542*, și **`hr_expense`** pentru fluxul generic *angajatul/firma plătește → (eventual) rambursare*.


# Integrarea cu `hr_expense` (prevenirea dublării cheltuielilor)

Întrucât cele două module pot coexista, există riscul ca aceeași cheltuială să fie contabilizată de două ori
(o dată prin Decont și o dată prin `hr_expense`). Pentru a preveni acest lucru:

- Pe formularul decontului, butonul **"Preia cheltuieli HR"** (disponibil în stările Draft/Advance) deschide
  un wizard cu cheltuielile `hr.expense` eligibile ale angajatului (aprobate/depuse, fără notă contabilă proprie,
  nelegate de alt decont). Cheltuielile selectate devin linii de decont și sunt legate prin `expenses_deduction_id`.
- Cheltuielile `hr.expense` au câmpul `expenses_deduction_id` care le leagă de un Decont de cheltuieli. Când acesta
  este completat, `action_post` din modulul standard **sare postarea** acelei cheltuieli — notele contabile se
  generează exclusiv din Decont, iar butoanele de postare standard sunt ascunse. Cheltuielile **nelegate** se
  postează normal, ca de obicei.
- Fiecare linie de decont reține originea (`hr_expense_id`); la ștergerea liniei, cheltuiala `hr.expense` este
  eliberată automat și redevine disponibilă pentru fluxul standard.
- Fișa angajatului (`hr.employee`) are un buton smart **"Deconturi"** care afișează numărul deconturilor și
  deschide lista filtrată pentru acel angajat.

Astfel contabilizarea rămâne unică: ori prin Decont (pentru cheltuielile preluate), ori prin `hr_expense`
(pentru restul).


# Exemplu de Testare: Decontarea Cheltuielilor din Avans

## 🎯 Obiectivul Testului
Decontarea corectă a unui avans de **1.000 RON**, cu cheltuieli totale de **800 RON**, rezultând în **restituirea diferenței** de **200 RON** de către angajat.

## ⚙️ Pașii de Testare (Scenariu)

| Pas | Acțiune Utilizator (Tester) | Rezultat Așteptat (Verificare) |
|---|---|---|
| **1. Acordare Avans** | Se înregistrează acordarea unui avans de 1.000 RON angajatului X. | Soldul contului **542** (Avansuri de decontat) crește cu 1.000 RON. |
| **2. Creare Decont** | Angajatul X inițiază un nou decont, făcând referire la avansul primit. | Decontul preia automat valoarea avansului de 1.000 RON. |
| **3. Introducere Cheltuieli** | Se introduc cheltuielile: Cazare (500 RON, TVA inclus) și Transport (300 RON, TVA inclus). | Total cheltuieli = **800 RON**. Se calculează corect TVA-ul deductibil. |
| **4. Validare Calcul** | Se verifică automat calculul diferenței. | **Avans (1.000) - Cheltuieli (800) = Diferență de restituit (200 RON)**. |
| **5. Aprobare Decont** | Decontul este trimis și aprobat de toți factorii decizionali. | Statutul decontului se schimbă în "**Aprobat/Decontat**". |
| **6. Restituire Avans** | Angajatul restituie diferența de 200 RON (înregistrare la Casierie/Bancă). | Se generează documentul de încasare (Chitanță/Dispoziție de Încasare). |
| **7. Contabilizare Finală** | Sistemul contabilizează decontul și restituirea. | Contul **542** al angajatului se închide (Sold **0**). |

---

## 📝 Note Contabile Aferente

Acestea sunt notele contabile așteptate pentru a testa închiderea corectă a avansului (Contul 542 - Avansuri de decontat):

| Nr. Crt. | Operațiune | Cont Debitor | Cont Creditor | Suma (RON) | Explicație |
|---|---|---|---|---|---|
| **1** | Acordare Avans | **542** (Avans X) | **5311/5121** (Casa/Banca) | 1.000 | Acordarea avansului. |
| **2** | Decontare Cheltuieli | **6xx** (Cheltuieli) | **542** (Avans X) | 672.27 | Valoarea cheltuielilor fără TVA (ex: 800 - 127.73). |
| | | **4426** (TVA Deductibil) | **542** (Avans X) | 127.73 | TVA aferent cheltuielilor (ex: 19%). |
| **3** | Restituire Sold | **5311/5121** (Casa/Banca) | **542** (Avans X) | 200 | Diferența restituită de angajat. |

**Verificare Sold Final Cont 542 (Avans X):**
* **Total Debitor:** 1.000 RON
* **Total Creditor:** 800 RON (Cheltuieli) + 200 RON (Restituire) = 1.000 RON
* **Sold Final:** 1.000 (D) - 1.000 (C) = **0 RON (Corect)**
