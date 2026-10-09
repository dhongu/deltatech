# Fișă Modul: Încasarea comenzilor de vânzare

**Modul:** `deltatech_sale_payment`
**Utilizator principal:** Operator vânzări / magazin online, casier, contabil care urmărește încasările
**Prioritate:** 🟡 Medie (necesar oriunde clienții plătesc înainte de livrare — transfer bancar, ramburs, card — și vânzările trebuie să știe ce comenzi sunt achitate)

---

## 1. Scop business

În Odoo standard, o comandă de vânzare nu spune **cât s-a încasat** pe ea: suma plătită apare pe
factură, iar tranzacțiile de plată (card, transfer bancar, ramburs) stau într-un ecran separat. Când
clientul plătește prin transfer bancar sau în numerar, operatorul nu are niciun gest simplu prin care
să marcheze încasarea direct pe comandă.

Modulul rezolvă ambele probleme:

- **pe fiecare comandă** se vede **Încasare** (suma încasată, în moneda comenzii), **procesatorul** de
  plată și **Stare încasare** (Fără, Inițiată, În așteptare, Autorizată, Parțială, Efectuată, Anulată);
- **lista comenzilor** se poate filtra, grupa și sorta după starea încasării — „ce comenzi au plata în
  așteptare?", „ce comenzi sunt achitate integral și pot pleca?";
- acțiunea **Confirmă încasarea** marchează pe comandă o încasare primită în afara unui procesator
  online (transfer bancar văzut pe extras, ramburs), fără a trece prin ecranul de tranzacții.

Modulul urmărește **starea** încasării pe comandă. Plata contabilă se înregistrează în continuare de
contabilitate (vezi „Note de monografie și raportare").

## 2. Bază legală și context

Modul operațional, fără temei fiscal propriu. Starea încasării este o informație **de gestiune** pentru
vânzări și logistică (ce comandă se livrează), nu un document contabil.

Încasarea propriu-zisă, cu nota contabilă și documentul justificativ (extras de cont, chitanță,
borderou de ramburs), rămâne a contabilității: modulul **nu** emite chitanțe și **nu** postează note
proprii — vezi secțiunea 6, „Note de monografie și raportare".

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| **Operator vânzări / magazin online** | urmărește starea încasării în lista comenzilor, confirmă încasările prin transfer bancar |
| **Casier / responsabil ramburs** | confirmă încasarea comenzilor achitate la livrare |
| **Contabil** | verifică plățile create și reconcilierea lor cu facturile |
| **Administrator** | configurează procesatorii de plată și jurnalele lor |

Drepturi: acțiunea **Confirmă încasarea** apare utilizatorilor cu drept de **Vânzări** (nivel
**Utilizator: Numai documente proprii** sau mai mult). Cine poate modifica o comandă îi poate confirma
și încasarea; dreptul de **Facturare** nu este necesar. Fereastra verifică întâi dreptul de modificare
pe comandă, apoi scrie tranzacția în numele sistemului; tranzacția rămâne creată de utilizator. Un
vânzător cu **Numai documente proprii** confirmă încasarea pe comenzile lui; pe comanda altui vânzător
primește eroare de acces. Vânzătorii pot vedea tranzacțiile de plată, dar nu le pot modifica din
ecranul de tranzacții.

Roluri recomandate la testare: un **Utilizator Vânzări: Numai documente proprii**, fără drept de
Facturare, pentru confirmarea încasării pe comenzile lui, un al doilea vânzător (nu poate confirma pe
comenzile primului) și un **Contabil** pentru înregistrarea plății.

## 4. Conturi și date implicate

Modulul nu impune conturi și nu creează plăți. Contul în care ajung banii depinde de tipul
procesatorului — vezi „Note de monografie și raportare".

Cum se calculează **Încasare** (suma afișată pe comandă), în **moneda comenzii**:

- suma încasată pe **facturile validate** ale comenzii (total minus rest de plată; notele de credit
  scad), adusă în moneda comenzii la cursul de la data facturii;
- suma **tranzacțiilor confirmate** ale comenzii, adusă în moneda comenzii la data tranzacției;
- se ia **cea mai mare** dintre cele două. Aceiași bani apar de obicei de două ori (ca tranzacție și
  ca plată pe factură) și nu trebuie adunați; maximul nu dublează încasarea și nici nu pierde o
  tranzacție încă nedecontată pe factură.

Comanda devine **Efectuată** când suma încasată atinge totalul comenzii (la rotunjirea monedei) și
**Parțială** când s-a încasat ceva, dar mai puțin.

Date minime pentru demo:
- un procesator de plată activ (ex. **Transfer bancar**);
- un client și un produs cu preț;
- o comandă la care clientul a ales transfer bancar (tranzacție **În așteptare**).

## 5. Configurare inițială

1. **Instalați modulul** `deltatech_sale_payment`. La instalare, starea încasării se calculează pentru
   comenzile existente.
2. **Activați procesatorii** folosiți: **Facturare → Configurare → Plăți online → Furnizori de plată**
   (ex. **Transfer bancar**; meniul e vizibil administratorului contabil). Fereastra **Confirmă
   încasarea** propune doar procesatorii care nu sunt dezactivați.
3. Pentru procesatorii **electronici** (card, plăți online), verificați câmpul **Jurnal plată** din
   tabul **Configurare** al furnizorului: se completează automat cu primul jurnal de bancă (doar
   jurnale de bancă sunt permise). Pe jurnal, **Facturare → Configurare → Jurnale → <banca> → Plăți de
   Primit**, coloana **Conturi de încasări restante** de pe linia procesatorului: Odoo pune implicit
   contul **Încasări restante**, un analitic de 5121 creat la instalarea planului de conturi (581
   Viramente interne doar dacă acel cont lipsește). Pe 5121, banii încă nedecontați de procesator
   apar ca disponibil în bancă. Setați **5125 Sume în curs de decontare**, de preferat pe un analitic
   dedicat procesatorului (ex. 5125.01): 5125 este și contul de suspensie al extraselor în planul RO,
   iar fără analitic cele două se amestecă.
4. Opțional, în **Vânzări → Configurare → Setări**, bifați facturarea automată (eticheta în română:
   **Factură client Automată**), dacă doriți ca o comandă plătită printr-un procesator **electronic** să
   fie facturată automat. Același lucru se întâmplă și la **Transfer bancar**, după **Confirmă** în
   fereastră, dacă oferta a fost confirmată (vezi pasul 4).
5. Setați contul avansurilor: **Facturare → Configurare → Setări**, secțiunea **Conturi implicite** →
   **Conturi produse** → **Cont plată în avans** = **419 Clienți – creditori**. Planul RO nu îl
   completează; fără el, linia de avans a facturii merge pe contul de venit al produsului (70x), nu pe
   419. Contul e folosit și de factura de avans pe care Odoo o emite singur, cu facturarea automată
   bifată, când o comandă confirmată e încasată **parțial**.
6. În lista comenzilor, coloana **Stare încasare** este vizibilă implicit; **Procesator încasare** se
   adaugă din selectorul de coloane opționale.

## 6. Flux de utilizare

Scenariul: clientul **Magazin Exemplu SRL** a comandat 2 buc. × 500 lei + TVA (1.210,00 lei) și a ales
plata prin transfer bancar. Banii au intrat în cont, iar operatorul confirmă încasarea pe comandă.

### Pasul 1 — Comanda cu plata în așteptare

**Vânzări → Comenzi → Oferte** (sau **Comenzi**) → deschideți comanda.

Sub **Termene plată** apar informațiile adăugate de modul:
- **Încasare** — suma încasată până acum (aici **0,00 lei**) și, alături, procesatorul (**Transfer
  bancar**);
- **Stare încasare** — **În așteptare**: clientul a ales transferul bancar, dar banii nu au fost încă
  confirmați.

Culorile ajută la citire: verde = **Efectuată**, portocaliu = **Parțială / În așteptare / Inițiată /
Autorizată**, roșu = **Anulată**, gri = **Fără**.

![Comanda cu plata în așteptare](screenshots/01_comanda_plata_in_asteptare.png)

### Pasul 2 — Deschideți „Confirmă încasarea"

Pe formularul comenzii, apăsați pictograma **⚙** de lângă numărul comenzii (meniul de acțiuni) →
**Confirmă încasarea**.

![Meniul ⚙ al comenzii cu „Confirmă încasarea"](screenshots/02_meniu_actiuni_confirma_incasarea.png)

### Pasul 3 — Completați și confirmați încasarea

Se deschide fereastra **Confirmă încasarea**. Când comanda are o tranzacție **în așteptare** (cazul
nostru), fereastra o preia: **Tranzacție**, **Procesator încasare**, **Metodă de plată** și **Valoare**
sunt precompletate cu datele ei. Altfel, **Valoare** propune **restul de încasat** (totalul comenzii
minus **Încasare**) și completați procesatorul.

Fereastra nu modifică niciodată o tranzacție deja **confirmată**: pe o comandă încasată parțial adaugă o
tranzacție nouă pentru rest, iar pe una încasată integral propune 0 și nu face nimic. O comandă cu o
plată cu cardul **autorizată** este refuzată: autorizarea se capturează sau se anulează din procesator.

Verificați înainte de a confirma:
- **Valoare** este suma **efectiv încasată** (pe extras / în casă), nu neapărat totalul comenzii — o
  încasare mai mică lasă comanda **Parțială**;
- **Procesator încasare** este cel prin care au venit banii;
- **Dată încasare** este data de pe extras / din casă (implicit, ziua curentă).

Butoanele:
- **Confirmă** — tranzacția devine **confirmată**; comanda trece pe **Efectuată** (sau **Parțială**);
- **Adaugă** — înregistrează tranzacția **în așteptare**, fără confirmare (ex. clientul a anunțat plata,
  dar banii nu au intrat încă);
- **Renunță** — închide fereastra fără modificări.

**Dată încasare** se păstrează: în nota „Încasare de … prin … primită la …" din istoricul comenzii, în
mesajul de stare al tranzacției și, la procesatorii **electronici**, ca dată a plății contabile create
de Odoo. La **Transfer bancar** nu se creează, de regulă, plată (pasul 4); contabilul o înregistrează cu
data de pe extras.

![Fereastra „Confirmă încasarea"](screenshots/03_wizard_confirma_incasarea.png)

### Pasul 4 — Comanda încasată

După **Confirmă**, aceeași comandă (S00002) arată **Încasare 1.210,00 lei**, procesatorul **Transfer
bancar** și **Stare încasare: Efectuată** (verde).

Tranzacția se procesează imediat, ca la procesatorii electronici:
- oferta se **confirmă automat** când încasarea atinge procentul de plată în avans cerut pe ofertă
  (**Plată online**) sau, dacă oferta nu cere plată online, la orice încasare, chiar parțială; în
  ambele cazuri, doar dacă nu cere semnătură online. Odoo cere implicit
  semnătura (**Vânzări → Configurare → Setări → Semnătură online**), iar o ofertă nesemnată rămâne
  **Ofertă**: o confirmați cu **Confirmă** din antetul comenzii. Pe captură, compania de demo cere
  semnătura, deci comanda a rămas ofertă;
- cu facturarea automată bifată (secțiunea 5), comanda confirmată se facturează: factură finală la
  încasarea integrală, factură de avans la o încasare parțială;
- la **Transfer bancar** **nu** se creează plată contabilă: Odoo nu are metodă de plată contabilă pentru
  acest tip de procesator. Excepție: dacă jurnalul de bancă are o linie de metodă legată de procesator
  (se întâmplă pe baze migrate), Odoo creează plata; verificați în **Plăți de Primit** pe jurnal.
  Contabilul înregistrează încasarea pe factură sau la reconcilierea extrasului
  (vezi „Note de monografie și raportare").

![Comanda încasată integral](screenshots/04_comanda_incasata.png)

### Pasul 5 — Urmărirea încasărilor în lista comenzilor

**Vânzări → Comenzi → Comenzi**.

1. **Găsiți pe ecran** — coloana **Stare încasare** arată, pe fiecare rând, starea plății. Folosiți
   **Filtre** (Fără plată, Plată inițiată, Plată în așteptare, Plată autorizată, Plătită parțial, Plată
   efectuată, Plată anulată) sau **Grupează după → Stare încasare** pentru o imagine pe grupuri.
2. **Verificați** — comenzile **Plătită parțial** au un rest de încasat: deschideți comanda, restul
   este totalul minus **Încasare** din formular; comenzile **În așteptare** vechi de câteva zile sunt transferuri anunțate și neprimite,
   de urmărit cu clientul; **nicio** comandă cu plată în avans nu pleacă la livrare înainte de
   **Efectuată**.
3. **Treceți mai departe** — deschideți comanda de urmărit sau exportați lista (**selectați rândurile →
   ⚙ Acțiuni → Export**) pentru raportarea către contabilitate.

![Lista comenzilor grupată după starea încasării](screenshots/05_lista_grupata_stare_incasare.png)

### Note de monografie și raportare

Modulul **nu** postează note contabile. Ce înregistrează contabilitatea depinde de procesator și de
momentul încasării. Rândurile de mai jos presupun că **factura există deja** (sau că facturarea automată
o emite la confirmare); încasarea înainte de factură e tratată separat, mai jos.

| Caz | Cine creează plata | Debit | Credit | Sumă |
|---|---|---|---|---|
| **Transfer bancar** confirmat în fereastră | contabilul, din extras (reconciliere) sau **Înregistrare plată** pe factură, pe jurnalul de bancă | **5121** Conturi la bănci în lei | **4111** Clienți | 1.210,00 lei |
| Procesator **electronic** (card), cu **5125** configurat pe linia metodei (secțiunea 5) | Odoo, la procesarea tranzacției confirmate | **5125** Sume în curs de decontare | **4111** Clienți | suma tranzacției |
| … apoi decontarea procesatorului apare pe extras | contabilul, la reconcilierea extrasului | **5121** Conturi la bănci în lei | **5125** Sume în curs de decontare | suma netă decontată |
| … și comisionul reținut de procesator | contabilul, la aceeași reconciliere | **627** Cheltuieli cu serviciile bancare și asimilate | **5125** Sume în curs de decontare | comisionul |
| **Ramburs** la curier: borderoul curierului | contabilul | **461** Debitori diverși (curierul) | **4111** Clienți | suma încasată de curier |
| … apoi curierul virează banii | contabilul, la reconcilierea extrasului | **5121** Conturi la bănci în lei | **461** Debitori diverși | suma virată |
| … taxa curierului, reținută din suma virată | contabilul, din factura curierului | **624** / **628** + **4426** | **401** Furnizori | factura curierului |
| … compensarea taxei cu suma reținută | contabilul | **401** Furnizori | **461** Debitori diverși | taxa reținută |
| Încasare în **numerar** | contabilul / casierul, **Înregistrare plată** pe jurnalul de casă, cu chitanță sau bon | **5311** Casa în lei | **4111** Clienți | suma încasată |

După decontare, soldul 5125 al procesatorului trebuie să fie zero: un sold debitor rămas înseamnă de
obicei un comision neînregistrat. La fel, soldul 461 al curierului trebuie să fie zero după virare și
compensarea taxei. TVA-ul pe comisionul procesatorului și pe cel al curierului depinde de
regimul fiecărui furnizor (ex. taxare inversă la un procesator din UE) și se stabilește cu contabilul.

⚠️ Fără configurarea de la secțiunea 5, procesatorii electronici debitează contul **Încasări restante**
(analitic de **5121**): bani încă nedecontați apar ca disponibil în bancă, iar 5121 nu se mai potrivește
cu extrasul. Încasările pe drum aparțin contului 5125.

**Încasare înainte de factură (avans).** Scenariul tipic al modulului este plata înainte de livrare.
Dacă banii intră înainte de emiterea facturii (fără facturare automată, sau cu facturare automată la o
încasare parțială), suma încasată este un **avans**: TVA-ul devine exigibil la data încasării (Cod fiscal, art. 282 alin. (2)), deci se emite o
factură de avans, iar avansul se regularizează pe factura finală. Cu facturarea automată bifată, la o
încasare parțială Odoo emite singur factura de avans; altfel o emiteți din comandă. Linia de avans merge
pe **419** doar cu **Cont plată în avans** setat (secțiunea 5, pasul 5). La o companie cu TVA la
încasare, TVA-ul facturii de avans merge pe **4428**, nu pe 4427.

| Operațiune | Debit | Credit |
|---|---|---|
| Factura de avans (din comandă: **Crează factura → Plată în avans (procent)** sau **(valoare fixă)**) | **4111** Clienți | **419** Clienți – creditori + **4427** TVA colectată (21%) |
| Încasarea avansului | **5121** (sau **5125** la procesator electronic) | **4111** Clienți |
| Factura finală, cu regularizarea avansului | **4111** Clienți | **707** / **704** + **4427**, iar avansul se reia cu minus pe **419** și **4427** |

Pentru gestiunea facturilor de avans pe planul RO, vezi modulul `l10n_ro_advance_invoice`.

Numerarul nu trece printr-un procesator cu plată automată: jurnalul unui furnizor de plată poate fi doar
de bancă. Fereastra poate marca starea comenzii, dar casa se înregistrează separat. Respectați și
plafoanele de încasare în numerar (Legea 70/2015).

Factura comenzii apare ca plătită după ce plata se **reconciliază** cu ea. Din acel moment, suma încasată
pe factură intră în **Încasare** (secțiunea 4), fără să se adune cu tranzacția confirmată.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale`, `payment` (standard) | comanda, tranzacțiile și procesatorii de plată |
| `account_payment` (standard) | plata contabilă creată la procesarea tranzacțiilor electronice confirmate |
| `payment_custom` (standard) | procesatorul **Transfer bancar** |
| `deltatech_website_sale_status` | folosește **Stare încasare** în lista comenzilor online neîncasate |
| `deltatech_sale_store` | chitanțele de magazin intră în calculul sumei încasate |

**Ce e automat:** suma încasată, starea și procesatorul pe comandă (recalculate la orice schimbare a
tranzacțiilor sau facturilor). Pentru procesatorii **electronici**, Odoo standard confirmă oferta
(când încasarea atinge plata în avans cerută, vezi pasul 4), creează plata și, opțional, factura.

După **Confirmă încasarea** pe **Transfer bancar**, la fel: oferta se confirmă (dacă nu cere
semnătură online) și, opțional, se facturează, fără plată contabilă.

Procesatorul **Plată la livrare** (din magazinul online) se comportă ca **Transfer bancar**: nici el nu
are metodă de plată contabilă, deci Odoo nu creează plată. Rambursul se înregistrează de contabil prin
461 (vezi „Note de monografie și raportare").

**Ce rămâne manual:** confirmarea încasărilor primite prin transfer bancar sau ramburs; la acestea,
plata contabilă și confirmarea ofertelor care cer semnătură online; facturile de avans pentru
încasările dinaintea facturii; încasările în numerar; reconcilierea extrasului și comisioanele
procesatorilor.

## 8. Verificări pentru consultant

- [ ] O comandă nouă, fără tranzacții, arată **Stare încasare: Fără** și **Încasare 0,00**.
- [ ] Comanda cu transfer bancar ales arată **În așteptare**, procesatorul **Transfer bancar**, și apare
      la filtrul **Plată în așteptare**.
- [ ] **⚙ → Confirmă încasarea** preia tranzacția în așteptare (procesator, metodă, valoare
      precompletate).
- [ ] **Confirmă** cu valoarea integrală: comanda trece pe **Efectuată**, **Încasare** = totalul
      comenzii.
- [ ] **Confirmă** cu jumătate din valoare pe o altă comandă: **Parțială**, iar comanda apare la
      **Plătită parțial**.
- [ ] **Adaugă** (fără confirmare): tranzacția rămâne **În așteptare**, starea comenzii nu devine
      Efectuată.
- [ ] O valoare negativă în fereastră e refuzată („Valoarea trebuie să fie pozitivă").
- [ ] Un vânzător cu **Numai documente proprii**, **fără** drept de Facturare, confirmă încasarea pe
      comanda lui; pe comanda altui vânzător primește eroare de acces.
- [ ] **Dată încasare** completată în fereastră apare în nota din istoricul comenzii.
- [ ] Pe o comandă încasată parțial, fereastra propune restul și adaugă o tranzacție nouă; tranzacția
      confirmată anterior rămâne neschimbată. Pe o comandă **Efectuată** propune 0.
- [ ] O comandă cu plată **Autorizată** este refuzată de fereastră.
- [ ] După **Confirmă** pe **Transfer bancar**: oferta se confirmă dacă nu cere semnătură online (altfel
      rămâne **Ofertă**), cu facturarea automată bifată apare factura, iar tranzacția nu rămâne în
      așteptare. Nu există plată contabilă (dacă jurnalul nu are linie de metodă pentru procesator);
      contabilul înregistrează plata pe factură (Dr 5121 / Cr 4111).
- [ ] O ofertă **fără** plată online cerută, încasată **parțial** prin fereastră, se confirmă (dacă nu
      cere semnătură online); cu plată online cerută de 50%, o încasare de 30% o lasă **Ofertă**.
- [ ] Pe un procesator electronic, linia metodei din jurnalul de bancă are **5125**, nu contul implicit
      **Încasări restante** (5121xx); plata creată la procesare are Dr 5125 / Cr 4111.
- [ ] După decontarea procesatorului (net + comision 627), soldul 5125 al procesatorului este zero.
- [ ] **Cont plată în avans** = 419 în setări; o încasare înainte de factură are factură de avans cu
      linia de avans pe **419** (+ 4427), iar factura finală regularizează avansul.
- [ ] Cu facturarea automată bifată, o comandă confirmată încasată parțial primește automat o factură
      de avans, pe 419.
- [ ] Comandă de 100 EUR într-o companie în lei, facturată și încasată 50 EUR pe factură: **Încasare
      50,00 €**, **Parțială** (nu 250 și nu Efectuată).
- [ ] Factură încasată integral printr-o tranzacție: **Încasare** = totalul, **nu** dublul lui.
- [ ] **Grupează după → Stare încasare** în lista comenzilor dă un grup pe fiecare stare.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|-----------------|-------|-----------|
| „Vă rog să selectați o comandă de vânzare" | Fereastra a fost deschisă fără o comandă activă | Deschideți-o din formularul comenzii, **⚙ → Confirmă încasarea** |
| „Valoarea trebuie să fie pozitivă" | Valoare negativă în fereastră | Introduceți suma încasată, pozitivă; un retur de bani se face din factură / nota de credit |
| „Ups! Se pare că ai dat peste niște înregistrări strict confidențiale. Ne pare rău, … nu are acces de «write» la: …" la **Confirmă** / **Adaugă** | Vânzătorul are **Numai documente proprii**, iar comanda e a altui vânzător | Confirmarea o face vânzătorul comenzii sau un utilizator cu **Toate documentele** |
| Comanda e **Efectuată**, dar nu există plată contabilă | Procesator **Transfer bancar** sau **Plată la livrare**: Odoo nu creează plată pentru ei (dacă jurnalul nu are linie de metodă pentru procesator) | Contabilul înregistrează plata din extras sau pe factură |
| Comanda e **Efectuată**, dar a rămas **Ofertă** | Oferta cere semnătură online și nu e semnată | Confirmați comanda din antetul ei |
| Plata cardului debitează contul **Încasări restante** (5121xx) | Linia metodei procesatorului are contul implicit | Setați **5125** pe linia metodei (secțiunea 5) |
| Sold debitor rămas pe 5125 după decontarea procesatorului | Comisionul reținut de procesator nu a fost înregistrat | Înregistrați comisionul pe 627 la reconcilierea extrasului |
| „Procesatorul de plată … aparține altei companii decât comanda …" | Utilizatorul are mai multe companii active și a ales în fereastră procesatorul altei companii | Alegeți procesatorul companiei comenzii. Atenție: în versiunea actuală e refuzat și procesatorul companiei-mamă pe comanda unei sucursale |
| „Metoda de plată … nu este disponibilă pentru procesatorul …" | În fereastră s-a ales o metodă de plată care nu aparține procesatorului (ex. Card pe Transfer bancar) | Alegeți o metodă a procesatorului sau lăsați câmpul gol |
| „Tranzacția … nu aparține comenzii …" | Apare doar din integrări sau cod personalizat, care trimit ferestrei o tranzacție a altei comenzi | Corectați integrarea; din formularul comenzii mesajul nu apare |
| Pe o comandă **Efectuată**, fereastra propune **Valoare 0** | Comanda e încasată integral; fereastra propune doar restul de încasat | Nimic de confirmat. O încasare suplimentară se completează manual și se adaugă ca tranzacție nouă |
| „Comanda are o plată autorizată (…). Capturați-o sau anulați-o din procesatorul de plată." | Comanda are o plată cu cardul **Autorizată**, încă necapturată | Capturați sau anulați plata din procesator; fereastra nu o înlocuiește |
| „Tranzacția … nu mai așteaptă plata." | Tranzacția preluată de fereastră a fost confirmată sau anulată între timp (de procesator sau de alt utilizator) | Închideți și redeschideți fereastra: propune restul de încasat |
| **Încasare** pare prea mică la o comandă plătită cu cardul și completată cu plată pe factură | Se ia maximul dintre facturi și tranzacții, nu suma lor, cât timp decontarea cardului nu e reconciliată | Reconciliați decontarea procesatorului pe factură |

## 10. Capturi de ecran

Capturile (`readme/screenshots/`) sunt **generate automat** din `tests/test_screenshots.py` (mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, import defensiv), în **limba română**, pe planul de
conturi RO, pe compania „Demo Încasări SRL" în RON:

| # | Fișier | Conținut |
|---|--------|----------|
| 1 | `screenshots/01_comanda_plata_in_asteptare.png` | Comanda de 1.210,00 lei cu **Încasare 0,00**, procesator **Transfer bancar**, **Stare încasare: În așteptare** |
| 2 | `screenshots/02_meniu_actiuni_confirma_incasarea.png` | Meniul **⚙** de lângă numărul comenzii, deschis, cu **Confirmă încasarea** |
| 3 | `screenshots/03_wizard_confirma_incasarea.png` | Fereastra **Confirmă încasarea** precompletată din tranzacția în așteptare |
| 4 | `screenshots/04_comanda_incasata.png` | Aceeași comandă după **Confirmă** în fereastră: **Încasare 1.210,00 lei**, **Stare încasare: Efectuată** |
| 5 | `screenshots/05_lista_grupata_stare_incasare.png` | Lista comenzilor grupată după **Stare încasare** (Efectuată, Parțială, În așteptare, Fără) |

Regenerare (planul de conturi RO este necesar pentru compania de demo):

```bash
./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_sale_payment,payment_custom,l10n_ro,l10n_ro_doc_screenshots --test-tags=fise_screenshots --stop-after-init --http-port=8987 --gevent-port=8988
```

## 11. Observații pentru manual

Prezentați **Stare încasare** ca instrumentul zilnic al operatorului: lista comenzilor filtrată pe
**Plată în așteptare** și **Plătită parțial** este lista de urmărit cu clienții, iar **Efectuată** este
semnalul că o comandă cu plată în avans poate pleca. Insistați pe patru lucruri: (1) **Încasare** e în
**moneda comenzii** și nu adună de două ori aceiași bani (tranzacție + plată pe factură); (2)
**Confirmă încasarea** marchează **starea**, nu înregistrează plata: la transfer bancar, contabilitatea
înregistrează plata din extras (și factura de avans, dacă banii vin înaintea facturii), iar oferta se
confirmă singură doar dacă nu cere semnătură online; (3)
fereastra propune restul de încasat, nu atinge tranzacțiile confirmate și refuză plățile cu cardul
autorizate; (4) confirmarea o poate face oricine are drept de modificare pe comandă, fără Facturare.
