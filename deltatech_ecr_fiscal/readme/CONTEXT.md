Câmpurile erau definite de două ori, identic: pe `pos.order` în `deltatech_pos` și pe
`account.move` în `deltatech_sale_store`. Orice consumator al lor trebuia să depindă de
unul din acele module, deci de întreaga suită de casă de marcat — chiar dacă nu voia
decât să citească numărul bonului.

Concret, asta a blocat puntea `l10n_ro_pos_fiscal_compliance_ecr` din suita de
localizare: dependența pe `deltatech_pos` nu se putea satisface în CI-ul acelei suite,
și rezolvarea dependențelor cădea înainte de teste.

Contractul stă acum într-un modul care depinde doar de `account`. Modulele de casă de
marcat rămân cele care **scriu** câmpurile; oricine altcineva le poate doar **citi**,
fără să atragă driverul.

Nici `point_of_sale` nu e în dependențe: mixinul pe `pos.order` îl aplică `deltatech_pos`,
care oricum depinde de POS. Altfel `deltatech_sale_store` — alternativa de magazin
**fără** POS — ar fi tras Point of Sale ca dependență obligatorie doar ca să ajungă la
câmpuri.

La instalare, un `pre_init_hook` preia rândurile din `ir_model_data` de la cele două
module donoare, ca actualizarea lor să nu ducă la ștergerea coloanelor și a numerelor de
bon fiscal deja înregistrate.
