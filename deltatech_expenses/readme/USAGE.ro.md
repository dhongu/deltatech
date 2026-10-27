1. În *Contabilitate > Furnizori > Expenses Deduction*, creați un decont pentru angajat, cu suma și
   data avansului, și apăsați **Advance**: avansul se înregistrează în contul 542 pe registrul de
   casă.
2. La întoarcere, adăugați bonurile ca linii (suma, taxa, furnizorul, contul) și, pentru o
   deplasare, numărul de zile de diurnă. Dacă angajatul a plătit din avans o factură a unui
   furnizor (de exemplu o factură mai veche), adăugați o linie de tip **Supplier Payment** cu acel
   furnizor (vezi mai jos).
3. Apăsați **Validate**: se contabilizează chitanțele de achiziție, decontarea lor din 542,
   diurna și plata diferenței, iar decontul trece în starea **Efectuat**.
4. **Invalidate** anulează un decont validat, ca să poată fi corectat.

**Liniile Supplier Payment.** La validare plata se înregistrează **Dr 401 = Cr 542** și se
reconciliază automat cu facturile deschise ale furnizorului pe același cont de datorii (întâi cele
mai vechi), deci factura devine plătită sau parțial plătită fără nicio legare manuală. Dacă plata
depășește facturile deschise, diferența este un avans acordat furnizorului și se trece pe **4092**
(Dr 4092 = Cr 401); la primirea facturii, contabilul compensează avansul (Dr 401 = Cr 4092). Dacă
planul de conturi nu are contul 4092, diferența rămâne ca sold debitor pe 401. Invalidarea
decontului șterge plata și reconcilierea, iar factura redevine deschisă.

Exemplu: un avans de 1.000 RON și bonuri de 800 RON lasă 200 RON de restituit de către angajat;
după validare, soldul contului 542 al angajatului este zero.
