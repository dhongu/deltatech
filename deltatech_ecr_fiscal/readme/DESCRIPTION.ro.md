Definește, într-un singur loc, câmpurile care păstrează rezultatul tipăririi pe o casă de marcat
fiscală (ECR/AMEF):

- **Bon fiscal (BF)**: Numărul bonului în raportul Z curent; reîncepe la fiecare Z.
- **Document fiscal (NR)**: Numărul documentului fiscal, unic pe aparat; cel de folosit când un
  document trebuie identificat fără ambiguitate.
- **Raport Z**: Numărul raportului Z din care face parte bonul.
- **Starea fiscală**: Rezultatul raportat de driverul aparatului.
- **Eroare fiscală**: Mesajul de eroare, când aparatul a refuzat sau a eșuat.

Câmpurile sunt adăugate aici pe **notele contabile** și, prin modulul `deltatech_pos`, pe
**comenzile POS**, prin mixinul abstract `deltatech.ecr.fiscal.mixin`.

Le scrie driverul (ecranul de plată POS sau acțiunea de tipărire din magazin, după răspunsul
agentului Terrabit Connect) și le citesc toate modulele de după: rapoartele, modulele de
conformitate fiscală, localizarea românească.

Modulul depinde doar de `account`, nu de `point_of_sale`, astfel încât câmpurile pot fi folosite
și de suitele care nu au acces la modulele de casă de marcat, și de alternativa de magazin fără
POS (`deltatech_sale_store`), fără să atragă Punctul de vânzare.

### De ce un modul separat

Câmpurile erau definite de două ori, identic: pe `pos.order` în `deltatech_pos` și pe
`account.move` în `deltatech_sale_store`. Orice modul care voia doar să citească numărul bonului
trebuia să depindă de unul dintre ele, deci de întreaga suită de casă de marcat.

Contractul stă acum într-un modul care depinde doar de `account`. Modulele de casă de marcat
rămân cele care **scriu** câmpurile; oricine altcineva le poate doar **citi**, fără să atragă
driverul. La instalare, un `pre_init_hook` preia rândurile din `ir_model_data` de la cele două
module, ca actualizarea lor să nu ducă la ștergerea coloanelor și a numerelor de bon fiscal deja
înregistrate.
