# Roadmap

Elemente identificate la revizuirea de cod (code review), de tratat ulterior. Sunt ordonate după
severitate. Niciunul nu blochează fluxul principal (avans → decont → diurnă → închidere 542), validat
prin teste.

## Corectitudine

- **Liniile de tip „Plată furnizor" (`supplier_payment`) nu se reconciliază.** La validare, nota de
  decontare `Dr 401 = Cr 542` generată pentru o linie `supplier_payment` nu este reconciliată (spre
  deosebire de liniile de tip „Cheltuieli", care se reconciliază cu chitanța). Contul 401 al
  furnizorului rămâne deschis, iar 542 nu se închide la zero pentru acest tip de linie. În plus, dacă
  partenerul nu are cont de furnizor configurat, nota poate eșua la postare. *De decis: reconciliere
  cu un document furnizor existent sau eliminarea tipului `supplier_payment` dacă nu mai e folosit.*

- **Import multi-monedă.** La preluarea unei `hr.expense` în altă monedă decât a companiei, linia
  primește suma în moneda companiei dar `currency_id` = moneda cheltuielii — nepotrivire care produce
  subtotal/TVA greșite. *De adăugat conversia corectă sau preluarea sumelor în moneda cheltuielii.*

- **TVA mixt la import.** Detecția `price_include` este „totul-sau-nimic"
  (`all(taxes.price_include)`). O cheltuială cu o taxă inclusă + una „pe deasupra" simultan este
  mapată greșit. *De tratat per-taxă (caz rar).*

- **`set_paid` tace la reziduu.** Marchează chitanța „plătită" doar dacă soldul este exact zero; la
  diferențe de rotunjire/valută rămâne tăcut neplătită, fără semnalare. *De adăugat verificare/avertizare.*

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
