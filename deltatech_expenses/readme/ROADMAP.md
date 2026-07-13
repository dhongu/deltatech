# Roadmap

Elemente identificate la revizuirea de cod (code review), de tratat ulterior. Sunt ordonate după
severitate. Niciunul nu blochează fluxul principal (avans → decont → diurnă → închidere 542), validat
prin teste.

## Semnalate de client (tichet POPVAL-COS) — REZOLVATE în 19.0.3.1.0

Verificate în cod pe 2026-07-10, toate confirmate și fixate (teste dedicate în `tests/test_expenses.py`):

- **Linia de credit 542 pe partenerul furnizorului, nu al angajatului** — FIXAT.
  `_create_advance_settlement` pune acum `partner_id` = partenerul angajatului (`expenses.partner_id`)
  pe linia de 542; doar linia de 401 rămâne pe furnizor. Test `test_advance_settlement_542_line_uses_employee_partner`.

- **TVA inclus în preț calculat greșit la validare** — FIXAT. `validate_expenses` trimite acum
  brutul (`line.amount`) ca `price_unit` când taxele sunt `price_include`, nu netul
  (`line.price_subtotal`). Test `test_validate_expenses_price_include_tax_document_total` verifică
  totalul documentului postat, nu doar linia.

- **Risc de dublă contabilizare** — FIXAT. `validate_advance`/`validate_expenses`/`invalidate_expenses`
  verifică explicit starea curentă și resping cu `UserError` o reapelare peste un decont deja
  procesat. Teste `test_validate_advance_rejects_second_call`, `test_validate_expenses_rejects_second_call`,
  `test_invalidate_requires_done_state`.

- **Reconciliere prea largă la plata directă către furnizor** — FIXAT (parțial). `_reconcile_supplier_payment`
  filtrează acum și pe `company_id`. Potrivirea exactă pe document de origine rămâne un gol cunoscut
  (vezi mai jos). Test `test_reconcile_supplier_payment_scoped_to_company`.

- **Import hr.expense fără re-validare la nivel de model** — FIXAT. `_import_hr_expenses` re-validează
  explicit (angajat/companie/stare/fără notă) orice i se dă, indiferent de ce trimite wizardul;
  domeniul din view-ul wizardului a fost restrâns. `sudo()` la legare a fost păstrat deliberat — vezi
  nota de mai jos. Test `test_import_hr_expenses_rejects_mismatched_employee`.

- **Acces necontrolat pe roluri** — FIXAT. Trei grupuri noi (`group_expenses_user`/`_approver`/`_accounting`,
  ierarhie prin `implied_ids`), acces CRUD diferențiat în `ir.model.access.csv`, regulă de acces
  „doar decontul propriu" pentru rolul de bază, verificare explicită de rol în cod pentru
  `validate_advance` (Aprobator+) și `validate_expenses`/`invalidate_expenses`/`unlink` (Contabil),
  butoane gated pe grup în view, câmpuri noi `approved_by_id`/`accounted_by_id`. Migrare
  `19.0.3.1.0` acordă rolul Contabil tuturor userilor existenți (compatibilitate upgrade) —
  administratorul trebuie să revizuiască și să restrângă rolurile per utilizator. Test
  `test_role_separation_advance_and_validate`.

- **Diurnă fără validare de plafon legal** — necesită modulul dedicat `l10n_ro_expense_allowance`
  (neinstalat la acest client); comunicat clientului, nu modificat în modulul de bază.

**Notă despre `sudo()`:** păstrat deliberat în `_import_hr_expenses` (legarea `hr.expense`) și în
corpul `validate_advance`/`validate_expenses`/`invalidate_expenses` (după verificarea explicită de
rol) — altfel un Aprobator/Contabil ar avea nevoie și de grupurile standard de Contabilitate/Jurnale
doar ca să poată apăsa butoanele acestui modul. Sudo e sigur aici pentru că rulează DUPĂ o validare
explicită de business (eligibilitate hr.expense / rol pe deducție), nu în locul ei.

## Runda 2 — verificare independentă a clientului (19.0.3.2.0)

Clientul a testat 19.0.3.1.0 independent (17 teste proprii, 0 eșecuri) și a semnalat 10 observații
suplimentare. Verificate în cod pe 2026-07-11:

- **Liniile de decont fără reguli proprii de acces** — FIXAT. Adăugate `ir.rule` pe
  `deltatech.expenses.deduction.line` (multi-company + „doar liniile decontului propriu" pentru
  Angajat + acces complet pentru Aprobator/Contabil), mirror pe regulile de la părinte — până acum
  restricția exista doar pe `deltatech.expenses.deduction`. Test `test_expenses_line_own_rule_restricts_access`.

- **`_import_hr_expenses` nu verifica starea decontului** — FIXAT (ratat în runda 1). Doar
  `action_open_import_hr_expenses` verifica `state in (draft, advance)`; `action_import`-ul
  wizard-ului și `_import_hr_expenses` apelate direct nu verificau, deci un decont deja
  Finalizat/Anulat putea încă primi linii noi. Adăugat guard explicit. Test
  `test_import_hr_expenses_rejects_when_deduction_not_open`.

- **`_default_account_diem` folosea `company_id` pe `account.account`** — FIXAT (bug pre-existent,
  nu introdus în runda 1). În O19 câmpul e `company_ids` (many2many); căutarea pe `company_id`
  arunca `ValueError`, prins tăcut de un `except Exception` care mascase complet eroarea — contul
  de diurnă implicit nu se completa niciodată automat. Corectat pe `company_ids`; eliminat și
  try/except-ul care înghițea eroarea (fail loud e mai sigur decât fail silent). Test
  `test_default_account_diem_uses_company_ids`.

- **`set_paid()` scria manual `payment_state`** — FIXAT prin eliminare. Metoda custom din
  `account_voucher.py` (override pe `account.move`, neexistentă în Odoo core) seta
  `payment_state = "paid"` direct când soldul era zero, în loc să lase Odoo să-l calculeze din
  reconciliere. Chitanța `in_receipt` intră deja în `is_invoice(include_receipts=True)`, deci
  `_compute_payment_state` standard se declanșează corect după `.reconcile()` — apelul și metoda au
  fost eliminate ca redundante și riscante. Testele existente (`test_supplier_payment_reconciles_open_bill`,
  `test_full_flow_advance_expense_refund_and_zero_542`) confirmă `payment_state` corect fără el.

- **Reconciliere fără potrivire pe document/sumă** — reconfirmat, rămâne pe roadmap (vezi mai jos).

- **Doar administratorii de sistem au rolul Contabil pe staging-ul clientului** — clarificat, nu e
  bug: migrarea `19.0.3.1.0` rulează doar la **upgrade** de pe o instalare anterioară (Odoo nu
  migrează la instalare nouă/fresh); pe o instalare fresh rămâne activ doar
  `base.group_system.implied_ids`, care acoperă doar adminii. Pe un upgrade real de producție
  (de pe 19.0.3.0.0/19.0.3.1.0 deja instalat), migrarea acordă rolul tuturor userilor interni
  existenți. De clarificat cu clientul dacă staging-ul e upgrade sau instalare nouă.

- **Sold istoric 542 / câmpuri aprobare necompletate pe deconturile vechi / OCR-Terrabit neadoptat
  în producție** — confirmate, dar în afara scopului acestui fix (date istorice, nu logică de cod);
  rămân subiect pentru planul de reconciliere separat discutat cu clientul.

## Corectitudine

- **Reconciliere supplier_payment fără potrivire exactă pe document/sumă.** După fix-ul de
  companie (mai sus), căutarea rămâne pe `partner_id`+`account_id`+stare deschisă — poate încă
  reconcilia cu o factură a aceluiași furnizor fără legătură reală cu decontul, dacă există mai
  multe facturi deschise. *De adăugat, unde e posibil, o corelare pe document de origine sau cel
  puțin pe sumă exactă înainte de reconciliere.*

- **Import multi-monedă.** La preluarea unei `hr.expense` în altă monedă decât a companiei, linia
  primește suma în moneda companiei dar `currency_id` = moneda cheltuielii — nepotrivire care produce
  subtotal/TVA greșite. *De adăugat conversia corectă sau preluarea sumelor în moneda cheltuielii.*

- **TVA mixt la import.** Detecția `price_include` este „totul-sau-nimic"
  (`all(taxes.price_include)`). O cheltuială cu o taxă inclusă + una „pe deasupra" simultan este
  mapată greșit. *De tratat per-taxă (caz rar).*

## Migrare

- **`partner_id` (related stored) vs. migrare.** Scriptul post-migrare setează `partner_id` prin SQL,
  dar câmpul este related stored la `employee_id.work_contact_id`. Pentru un angajat existent cu alt
  `work_contact_id`, o recalculare ulterioară poate suprascrie valoarea. *De aliniat work_contact_id
  la migrare sau de renunțat la store pe `partner_id`.*

## Curățenie / UX

- **Tab-ul „Plăți" rămâne gol.** `validate_expenses` nu mai creează `account.payment` (folosește note
  directe). Câmpul `payment_ids` și tab-ul aferent nu se mai populează, iar blocul de plăți din
  `invalidate_expenses` este cod mort. *De ascuns tab-ul / de legat la notele de decontare și de
  curățat codul mort.*

## Arhitectură

- **Dependența `hr_expense` este forțată la toate instalările.** Doar guard-ul `action_post` și
  wizardul de import au nevoie de `hr_expense`. *De evaluat mutarea acestui strat într-un modul-punte
  (`deltatech_expenses_hr`) auto-instalat când ambele module sunt prezente, ca să nu aducem stack-ul
  HR pe baze pur contabile.*
