1. În *Contabilitate > Furnizori > Expenses Deduction*, creați un decont pentru angajat, cu suma și
   data avansului, și apăsați **Advance**: avansul se înregistrează în contul 542 pe registrul de
   casă.
2. La întoarcere, adăugați bonurile ca linii (suma cu TVA inclus, furnizorul, contul) și, pentru o
   deplasare, numărul de zile de diurnă.
3. Contabilul apasă **Validate**: se contabilizează chitanțele de achiziție, decontarea lor din 542,
   diurna și plata diferenței, iar decontul trece în starea **Efectuat**.
4. **Invalidate** anulează un decont validat, ca să poată fi corectat.

**Plată furnizor.** O linie de tip *Supplier Payment* este o factură plătită de angajat din avans
(Dr 401 = Cr 542). Butonul **Bills Paid** de pe linie arată facturile furnizorului plătite, cu suma
alocată fiecăreia (se acceptă plata parțială); fără facturi alese, plata stinge întâi facturile
deschise cele mai vechi. Partea nealocată e un avans la furnizor, reclasificat Dr 4092 = Cr 401.

Exemplu: un avans de 1.000 RON și bonuri de 800 RON lasă 200 RON de restituit de către angajat;
după validare, soldul contului 542 al angajatului este zero.

**Mod de decontare.** *Numerar* plătește avansul din casă. *Virament (card personal)* îl plătește
dintr-un jurnal de bancă: Dr 542 = Cr 5125 (plăți în curs), reconciliat cu linia din extras
(Dr 5125 = Cr 5121); restituirea e Dr 5125 = Cr 542. *Card de firmă* nu are avans: chitanțele sunt
plătite de firmă, deci fiecare se decontează Dr 401 = Cr 5125 al jurnalului cardului și se
reconciliază cu extrasul cardului; angajatului i se datorează doar diurna, plătită din jurnalul de
plată. O retragere de numerar cu cardul de firmă e un decont separat *Virament* (Dr 542 = Cr 5121),
conform OMFP 1802/2014 pct. 302.

**Decont în valută.** Un decont pe un registru de casă în valută este ținut în moneda respectivă:
avansul, chitanțele, diurna și diferența se introduc în valută, iar fiecare notă contabilă are suma
în valută și contravaloarea în lei la cursul BNR din data ei (avansul la data avansului, fiecare
chitanță la data ei, diurna și diferența la data decontului — OMFP 1802/2014 pct. 319). La validare
542 se închide în valută, iar soldul rămas în lei se înregistrează ca diferență de curs:
Dr 665 = Cr 542 (nefavorabilă) sau Dr 542 = Cr 765 (favorabilă).
