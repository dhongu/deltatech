Punte între modulul standard de cheltuieli **`hr_expense`** și **`deltatech_expenses`** (Decont de
cheltuieli din avans de trezorerie, cont 542), pentru companiile care folosesc ambele fluxuri și vor
să evite dubla contabilizare a acelorași cheltuieli.

Se instalează **automat** (`auto_install`) doar atunci când ambele module — `deltatech_expenses` și
`hr_expense` — sunt prezente în baza de date. Companiile care nu folosesc modulul standard de
cheltuieli nu primesc acest modul, deci nu văd bifa „Cheltuieli" pe produs adusă de `hr_expense`
decât dacă chiar au nevoie de el.

Features:

- Buton **„Preia cheltuieli HR"** pe formularul Decontului (stările Ciornă/Avans): deschide un wizard
  cu cheltuielile `hr.expense` eligibile ale angajatului (aprobate/depuse, fără notă contabilă
  proprie, nelegate de alt decont) și le adaugă ca linii de decont.
- Acțiune contextuală pe lista de cheltuieli standard: „Adaugă în decont de cheltuieli" — trimite mai
  multe cheltuieli selectate către un decont ales.
- Cheltuielile `hr.expense` legate de un decont (`expenses_deduction_id`) nu se mai postează prin
  `action_post` standard — contabilizarea se face exclusiv prin Decont, evitând dublarea. Formularul
  cheltuielii arată un banner și ascunde butoanele de postare standard.
- La invalidarea unui decont, liniile importate din `hr.expense` se șterg automat, iar cheltuielile
  respective sunt eliberate — redevin disponibile pentru fluxul standard sau o nouă preluare.

Configurare: niciuna suplimentară — funcționează imediat ce ambele module sunt instalate.
