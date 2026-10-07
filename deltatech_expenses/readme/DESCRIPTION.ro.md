Avansuri de trezorerie pentru angajați, decontate cu un decont de cheltuieli, așa cum le
înregistrează contabilitatea din România: avansul se înregistrează în contul 542, angajatul aduce
bonurile, iar validarea decontului contabilizează chitanțele de achiziție, diurna și diferența de
restituit sau de plătit, până când contul 542 al persoanei ajunge la zero.

- **Avans în contul 542**: Avansul se plătește din registrul de casă și se înregistrează în
  contul 542 al angajatului.
- **Bonurile ca linii de decont**: Fiecare linie este un bon, cu TVA-ul calculat din taxa de pe
  linie; validarea creează chitanțele de achiziție și le decontează din avans. O linie poate fi și o plată către un
  furnizor făcută din avans.
- **Diurnă**: O sumă pe zi (implicit 42,5) înmulțită cu numărul de zile, înregistrată într-un cont
  de cheltuieli cu deplasările (implicit 625).
- **Diferența decontată**: Ce rămâne din avans este restituit de angajat, iar ce s-a cheltuit peste
  avans i se plătește angajatului, prin registrul de casă.
- **Decont tipărit**: Fiecare decont se poate tipări.

Modulul nu înlocuiește aplicația standard de cheltuieli (`hr_expense`), care rambursează
cheltuielile plătite de angajați și nu are avans de trezorerie. Cele două pot fi folosite în aceeași bază de date.
