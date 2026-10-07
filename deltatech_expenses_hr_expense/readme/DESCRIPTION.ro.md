Punte între aplicația standard de cheltuieli Odoo (`hr_expense`) și decontul de cheltuieli
Terrabit pentru avansuri de trezorerie (`deltatech_expenses`, cont 542), pentru companiile care
folosesc ambele fluxuri și vor să evite dubla contabilizare a acelorași cheltuieli.

- **Preluarea cheltuielilor HR în decont**: Butonul **Preia cheltuieli HR** de pe decont adaugă
  cheltuielile depuse sau aprobate ale angajatului ca linii de decont.
- **Trimitere din lista de cheltuieli**: Acțiunea **Adaugă în decont de cheltuieli** trimite
  dintr-o dată mai multe cheltuieli selectate către un decont ales.
- **Fără dublă contabilizare**: O cheltuială legată de un decont se contabilizează doar prin
  decont; butoanele ei de contabilizare sunt ascunse.
- **Eliberare la anulare**: La invalidarea decontului, liniile preluate se șterg, iar
  cheltuielile redevin disponibile.
- **Instalare automată**: Modulul se instalează singur când sunt prezente atât
  `deltatech_expenses`, cât și `hr_expense`; nu necesită configurare.
