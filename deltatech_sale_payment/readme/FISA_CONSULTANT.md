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
| **Operator vânzări / magazin online** | urmărește starea încasării în lista comenzilor, confirmă încasările prin transfer bancar (cu drept de Facturare) |
| **Casier / responsabil ramburs** | confirmă încasarea comenzilor achitate la livrare (cu drept de Facturare) |
| **Contabil** | verifică plățile create și reconcilierea lor cu facturile |
| **Administrator** | configurează procesatorii de plată și jurnalele lor |

Drepturi: fereastra **Confirmă încasarea** creează și modifică tranzacții de plată, iar Odoo dă acest
drept doar utilizatorilor cu acces la facturare (**Facturare / Contabilitate**, nivel **Facturare** sau
mai mult) și administratorilor. Un vânzător care are **doar** drepturi de vânzări primește eroare de
acces la **Confirmă** și **Adaugă**. Înlocuirea unei tranzacții autorizate (vezi secțiunea 9) cere
drept de ștergere pe tranzacții, adică administrator. Lista procesatorilor din fereastră se citește cu
dreptul **Vânzări / Utilizator: Numai documente proprii**.

Roluri recomandate la testare: un **Utilizator Vânzări cu drept de Facturare** pentru confirmarea
încasării, un **Utilizator Vânzări fără Facturare** (vede starea, nu poate confirma) și un
**Contabil** pentru înregistrarea plății.

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
   **581 Viramente interne**, pentru că planul RO nu are un cont de încasări în curs. Setați
   **5125 Sume în curs de decontare**.
4. Opțional, în **Vânzări → Configurare → Setări**, bifați facturarea automată (eticheta în română:
   **Factură client Automată**), dacă doriți ca o comandă plătită printr-un procesator **electronic** să
   fie facturată automat. La **Transfer bancar** facturarea automată nu se declanșează (vezi pasul 4).
5. În lista comenzilor, coloana **Stare încasare** este vizibilă implicit; **Procesator încasare** se
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

Pe formularul comenzii, **⚙ Acțiuni → Confirmă încasarea**.

![Meniul Acțiuni cu „Confirmă încasarea"](screenshots/02_meniu_actiuni_confirma_incasarea.png)

### Pasul 3 — Completați și confirmați încasarea

Se deschide fereastra **Confirmă încasarea**. Când comanda are deja o tranzacție în așteptare (cazul
nostru), fereastra o preia: **Tranzacție**, **Procesator încasare**, **Metodă de plată** și **Valoare**
sunt precompletate cu datele ei. Fără tranzacție, completați procesatorul și valoarea încasată.

Verificați înainte de a confirma:
- **Valoare** este suma **efectiv încasată** (pe extras / în casă), nu neapărat totalul comenzii — o
  încasare mai mică lasă comanda **Parțială**;
- **Procesator încasare** este cel prin care au venit banii.

Butoanele:
- **Confirmă** — tranzacția devine **confirmată**; comanda trece pe **Efectuată** (sau **Parțială**);
- **Adaugă** — înregistrează tranzacția **în așteptare**, fără confirmare (ex. clientul a anunțat plata,
  dar banii nu au intrat încă);
- **Renunță** — închide fereastra fără modificări.

⚠️ Câmpul **Dată încasare** se afișează, dar **nu** se salvează nicăieri: nici pe tranzacție, nici pe
o plată. Data încasării rămâne cea de pe extras, la înregistrarea plății de către contabilitate.

![Fereastra „Confirmă încasarea"](screenshots/03_wizard_confirma_incasarea.png)

### Pasul 4 — Comanda încasată

După **Confirmă**, aceeași comandă (S00002) arată **Încasare 1.210,00 lei**, procesatorul **Transfer
bancar** și **Stare încasare: Efectuată** (verde).

Ce **nu** se întâmplă singur la **Transfer bancar**:
- comanda rămâne **Ofertă**; o confirmați cu **Confirmă** din antetul comenzii;
- nu se creează **plată** contabilă și nici factură automată: contabilul înregistrează încasarea pe
  factură sau la reconcilierea extrasului (vezi „Note de monografie și raportare").

Motivul: Odoo nu are metodă de plată contabilă pentru procesatorii de tip transfer bancar, așa că
procesarea automată a tranzacției confirmate eșuează. În jurnalul serverului apare, la fiecare rulare a
acțiunii programate de procesare a plăților (la 10 minute, timp de 4 zile), mesajul „Please define a
payment method line on your payment.". Starea comenzii nu este afectată.

![Comanda încasată integral](screenshots/04_comanda_incasata.png)

### Pasul 5 — Urmărirea încasărilor în lista comenzilor

**Vânzări → Comenzi → Comenzi**.

1. **Găsiți pe ecran** — coloana **Stare încasare** arată, pe fiecare rând, starea plății. Folosiți
   **Filtre** (Fără plată, Plată inițiată, Plată în așteptare, Plată autorizată, Plătită parțial, Plată
   efectuată, Plată anulată) sau **Grupează după → Stare încasare** pentru o imagine pe grupuri.
2. **Verificați** — comenzile **Plătită parțial** au un rest de încasat (totalul comenzii minus
   **Încasare**); comenzile **În așteptare** vechi de câteva zile sunt transferuri anunțate și neprimite,
   de urmărit cu clientul; **nicio** comandă cu plată în avans nu pleacă la livrare înainte de
   **Efectuată**.
3. **Treceți mai departe** — deschideți comanda de urmărit sau exportați lista (**selectați rândurile →
   ⚙ Acțiuni → Export**) pentru raportarea către contabilitate.

![Lista comenzilor grupată după starea încasării](screenshots/05_lista_grupata_stare_incasare.png)

### Note de monografie și raportare

Modulul **nu** postează note contabile. Ce înregistrează contabilitatea depinde de procesator:

| Caz | Cine creează plata | Debit | Credit | Sumă |
|---|---|---|---|---|
| **Transfer bancar** confirmat în fereastră | contabilul, din extras (reconciliere) sau **Înregistrare plată** pe factură, pe jurnalul de bancă | **5121** Conturi la bănci în lei | **4111** Clienți | 1.210,00 lei |
| Procesator **electronic** (card), cu **5125** configurat pe linia metodei (secțiunea 5) | Odoo, la procesarea tranzacției confirmate | **5125** Sume în curs de decontare | **4111** Clienți | suma tranzacției |
| … apoi decontarea procesatorului apare pe extras | contabilul, la reconcilierea extrasului | **5121** Conturi la bănci în lei | **5125** Sume în curs de decontare | suma decontată |
| Încasare în **numerar** | contabilul / casierul, **Înregistrare plată** pe jurnalul de casă, cu chitanță sau bon | **5311** Casa în lei | **4111** Clienți | suma încasată |

⚠️ Fără configurarea de la secțiunea 5, procesatorii electronici debitează **581 Viramente interne**.
Contul 581 servește doar transferurilor între conturile proprii de trezorerie. Încasările pe drum
aparțin contului 5125.

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
încasată integral, creează plata și, opțional, factura.

**Ce rămâne manual:** confirmarea încasărilor primite prin transfer bancar sau ramburs; la acestea,
confirmarea comenzii, factura și plata contabilă; încasările în numerar; reconcilierea extrasului.

## 8. Verificări pentru consultant

- [ ] O comandă nouă, fără tranzacții, arată **Stare încasare: Fără** și **Încasare 0,00**.
- [ ] Comanda cu transfer bancar ales arată **În așteptare**, procesatorul **Transfer bancar**, și apare
      la filtrul **Plată în așteptare**.
- [ ] **⚙ Acțiuni → Confirmă încasarea** preia tranzacția în așteptare (procesator, metodă, valoare
      precompletate).
- [ ] **Confirmă** cu valoarea integrală: comanda trece pe **Efectuată**, **Încasare** = totalul
      comenzii.
- [ ] **Confirmă** cu jumătate din valoare pe o altă comandă: **Parțială**, iar comanda apare la
      **Plătită parțial**.
- [ ] **Adaugă** (fără confirmare): tranzacția rămâne **În așteptare**, starea comenzii nu devine
      Efectuată.
- [ ] O valoare negativă în fereastră e refuzată („Valoarea trebuie să fie pozitivă").
- [ ] Un vânzător **fără** drept de Facturare vede **Stare încasare**, dar primește eroare de acces la
      **Confirmă**; cu drept de Facturare, confirmarea trece.
- [ ] După **Confirmă** pe **Transfer bancar**, comanda rămâne **Ofertă** și nu există plată: contabilul
      înregistrează plata pe factură (Dr 5121 / Cr 4111).
- [ ] Pe un procesator electronic, linia metodei din jurnalul de bancă are **5125**, nu 581; plata
      creată la procesare are Dr 5125 / Cr 4111.
- [ ] Comandă de 100 EUR într-o companie în lei, facturată și încasată 50 EUR pe factură: **Încasare
      50,00 €**, **Parțială** (nu 250 și nu Efectuată).
- [ ] Factură încasată integral printr-o tranzacție: **Încasare** = totalul, **nu** dublul lui.
- [ ] **Grupează după → Stare încasare** în lista comenzilor dă un grup pe fiecare stare.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|-----------------|-------|-----------|
| „Vă rog să selectați o comandă de vânzare" | Fereastra a fost deschisă fără o comandă activă | Deschideți-o din formularul comenzii, **⚙ Acțiuni → Confirmă încasarea** |
| „Valoarea trebuie să fie pozitivă" | Valoare negativă în fereastră | Introduceți suma încasată, pozitivă; un retur de bani se face din factură / nota de credit |
| „Nu aveți dreptul…" (eroare de acces) la **Confirmă** / **Adaugă** | Utilizatorul are doar drepturi de vânzări, fără Facturare | Acordați nivelul **Facturare** sau lăsați confirmarea pe seama facturării |
| Comanda e **Efectuată**, dar nu există plată contabilă și oferta nu s-a confirmat | Procesator **Transfer bancar**: Odoo nu creează plată pentru el | Confirmați comanda manual; contabilul înregistrează plata din extras sau pe factură |
| În log, la 10 minute: „Please define a payment method line on your payment." | Procesarea automată a unei tranzacții **Transfer bancar** confirmate (vezi pasul 4) | Nu afectează comanda; dispare după 4 zile. Plata se înregistrează manual |
| Plata cardului debitează **581** | Linia metodei procesatorului are contul implicit | Setați **5125** pe linia metodei (secțiunea 5) |
| **Dată încasare** din fereastră nu apare nicăieri | Câmpul nu se salvează | Data corectă se pune pe plata înregistrată de contabilitate |
| Pe o comandă deja încasată, **Confirmă încasarea** propune din nou suma | Fereastra preia ultima tranzacție, inclusiv una deja confirmată, și la confirmare încearcă să o **șterge** și să creeze una nouă. Un utilizator cu Facturare primește eroare de acces (ștergerea cere administrator); la administrator, pe un procesator electronic, plata contabilă a vechii tranzacții rămâne și se creează **a doua plată**: încasarea apare de două ori pe 4111 | Nu redeschideți fereastra pe comenzi **Efectuate**. Dacă s-a întâmplat, contabilul anulează plata în plus |
| Pe o plată cu cardul **Autorizată**, **Confirmă** anulează autorizarea | Fereastra înlocuiește tranzacția autorizată cu o încasare manuală | Capturați plata din procesator, nu din fereastră |
| **Încasare** pare prea mică la o comandă plătită cu cardul și completată cu plată pe factură | Se ia maximul dintre facturi și tranzacții, nu suma lor, cât timp decontarea cardului nu e reconciliată | Reconciliați decontarea procesatorului pe factură |

## 10. Capturi de ecran

Capturile (`readme/screenshots/`) sunt **generate automat** din `tests/test_screenshots.py` (mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, import defensiv), în **limba română**, pe planul de
conturi RO, pe compania „Demo Încasări SRL" în RON:

| # | Fișier | Conținut |
|---|--------|----------|
| 1 | `screenshots/01_comanda_plata_in_asteptare.png` | Comanda de 1.210,00 lei cu **Încasare 0,00**, procesator **Transfer bancar**, **Stare încasare: În așteptare** |
| 2 | `screenshots/02_meniu_actiuni_confirma_incasarea.png` | Meniul **⚙ Acțiuni** deschis pe comandă, cu **Confirmă încasarea** |
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
înregistrează plata din extras, iar comanda se confirmă manual; (3) fereastra nu se folosește pe comenzi
deja **Efectuate** și nici pe plăți cu cardul autorizate; (4) confirmarea cere drept de **Facturare**.
