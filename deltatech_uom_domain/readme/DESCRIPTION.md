Până în 18.0, lista de unități de măsură dintr-un document conținea toate unitățile
din categoria unității produsului: creai o dată „10 buc" în categoria „Unitate" și
era disponibilă pe orice produs măsurat în bucăți.

Odoo 19.0 a eliminat categoriile (`uom.category`) și a înlocuit filtrarea cu o listă
explicită per produs - câmpul `uom_ids` („Împachetare"). Unitățile existente rămân în
baza de date după migrare, dar nu mai apar nicăieri până nu sunt legate, una câte una,
de fiecare produs în parte. Pe un catalog de zeci de mii de produse, reconfigurarea
nu e realistă, iar fiecare produs nou o cere din nou.

Modulul reface comportamentul dinainte de 19.0: în comenzile de achiziție și în
facturile de achiziție, lista de unități conține orice unitate convertibilă la unitatea
produsului.
Criteriul e cel folosit intern de Odoo pentru conversie - aceeași rădăcină de arbore
(`uom.uom._has_common_reference()`), care joacă exact rolul vechii categorii. Un
produs în bucăți oferă „Duzina", „10 buc", „100 buc"; nu oferă „kg".

Ce calculează standardul se păstrează: unitatea produsului, `uom_ids` și unitatea de
pe linia de furnizor rămân în listă. Modulul doar adaugă.

## De ce contează limita la același arbore

În 19.0, `uom.uom._compute_quantity()` nu mai validează nimic - parametrul
`raise_if_failure` a rămas în semnătură, dar corpul metodei nu îl folosește, iar pe
linii nu există nicio constrângere de compatibilitate. Domeniul câmpului a rămas
singurul lucru care împiedică o conversie fără sens. De aceea modulul lărgește
domeniul până la marginea arborelui de conversie, și nu mai departe.

## De ce nu și pe facturile de vânzare

Extinderea se aplică doar documentelor de achiziție. Facturile emise pleacă la ANAF prin
e-Factura, iar `uom.uom._get_unece_code()` cade pe codul `C62` („one/piece") pentru orice
unitate fără cod UNECE mapat. O factură emisă în „10 buc" ar declara cantitatea 2 cu
unitatea „bucată" - valoric corect, cantitativ fals. Același cod alimentează și
`codUnitateMasura` din e-Transport. Comenzile de achiziție nu se transmit la ANAF, iar
recepția se convertește oricum în unitatea produsului, deci pe fluxul de achiziție
problema nu apare.

Dacă totuși vă trebuie unitatea și pe vânzări, mai întâi mapați-i un cod UNECE real
(modulul `deltatech_uom_unece`) - altfel cantitatea transmisă către ANAF e falsă.

## Ce nu acoperă

Multiplul de pe regula de reaprovizionare și codurile de bare pe ambalaj citesc
`product.uom_ids`, nu domeniul câmpului - pentru ele unitatea tot trebuie trecută pe
produs. Vânzările, mișcările de stoc și rebutul sunt lăsate intenționat neatinse:
implicit, mișcarea de stoc generată de o achiziție se convertește oricum în unitatea
produsului (`_adjust_uom_quantities`, cât timp parametrul `stock.propagate_uom` nu e
activat), iar pe eCommerce numărul de unități disponibile schimbă comportamentul
butonului „Adaugă în coș".
