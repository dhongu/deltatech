# Fișă Modul: Ținte de achiziție pe producător și categorie

**Modul:** `deltatech_purchase_target`
**Utilizator principal:** Managerul de achiziții (definește țintele și urmărește realizatul);
managerul comercial (citește vânzările pe aceleași produse)
**Prioritate:** 🟡 Medie (raport de gestiune nou, fără efect asupra contabilității, dar folosit
pentru negocierea bonusurilor de volum cu producătorii)

---

## 1. Scop business

Un distribuitor are cu o parte din producători **acorduri comerciale cu ținte de achiziție**:
valori sau cantități pe trimestru, uneori defalcate pe categorii de produse. Atingerea lor aduce
bonusuri de volum. Până acum urmărirea se făcea în Excel, pe baza extraselor din facturi.

Modulul aduce țintele în Odoo. Pentru fiecare producător și an, managerul de achiziții introduce
ținta pe trimestre, global și pe categorii eCommerce. Raportul **Realizat vs. țintă** arată live,
din facturile de furnizor postate:
- cât s-a cumpărat în trimestru și cumulat de la începutul anului;
- procentul realizat și cât a rămas până la țintă;
- vânzările pe aceleași produse, ca să se vadă dacă marfa cumpărată se și vinde.

Din raport se vede unde trebuie completată achiziția ca să se atingă ținta și unde trebuie
susținută vânzarea ca să nu rămână stoc.

Modulul mai adaugă **Comparație cost furnizori** (prețul mediu de achiziție al aceluiași produs
la fiecare furnizor) și producătorul în **Analiza achizițiilor**.

## 2. Bază legală și context

Nu există un temei legal propriu. Țintele sunt clauze comerciale din contractele cu producătorii,
iar raportul este un instrument de analiză de gestiune, nu o situație contabilă sau fiscală.

Bonusul de volum primit la atingerea țintei se înregistrează separat, ca reducere comercială
primită (factură sau notă de credit de la furnizor), în afara acestui modul.

## 3. Utilizatori și roluri

| Rol | Ce face | Drept Odoo |
|---|---|---|
| Manager achiziții | definește țintele, citește **Realizat vs. țintă** și **Comparație cost furnizori** | **Achiziții / Administrator**; pentru comparația de cost și un drept de **Facturare** sau **Contabilitate (citire)** |
| Achizitor | vede țintele și realizatul din formularul țintei (butonul **Realizat**) | **Achiziții / Utilizator** |
| Manager comercial | deschide vânzările din spatele cifrelor | **Vânzări / Administrator** sau dreptul de raport de marjă (*Sale Margin*) |
| Responsabil nomenclator | completează producătorul și categoriile eCommerce pe produse | privilegiul **Produse** pe nivelul **Creează** |

Meniul **Achiziții → Raportare** este vizibil doar administratorilor de achiziții (regula standard
Odoo). Achizitorul simplu ajunge la realizat doar din formularul țintei.

Roluri recomandate pentru testare: un administrator de achiziții (vede tot) și un achizitor simplu
(vede țintele doar în citire, fără meniul de raportare).

## 4. Conturi și date implicate

Modulul nu are conturi proprii și nu creează note contabile. Realizatul se citește din liniile de
produs ale facturilor de furnizor postate: valoarea fără TVA, în moneda companiei, la data
contabilă a facturii. Vânzările vin din **Raport analiză profit** (*Sale Margin*).

Date minime pentru demo (folosite și în capturi):
- Compania **Demo Distribuție SRL**, plan de conturi RO, monedă RON, an 2026.
- Producătorul **Nord Computers SRL**, marcat **Este producător**, și redistribuitorul
  **IT Distribuție SRL** (furnizor obișnuit).
- Categoriile eCommerce **Laptopuri** și **Accesorii**, cu subcategoria **Accesorii / Docking**.
- Produsele **Laptop 14"** (categoria **Laptopuri**) și **Docking USB-C** (categoriile
  **Laptopuri** și **Accesorii / Docking**), ambele cu producătorul Nord Computers SRL.

Facturi:

| Data | Partener | Document | Produs | Cant. | Valoare fără TVA |
|---|---|---|---|---|---|
| 10.02.2026 | Nord Computers SRL | factură furnizor | Laptop 14" | 10 | 28.000,00 lei |
| 10.02.2026 | Nord Computers SRL | factură furnizor | Docking USB-C | 5 | 1.500,00 lei |
| 15.02.2026 | Birotica Plus SRL | factură client | Laptop 14" | 3 | 10.500,00 lei |
| 15.03.2026 | IT Distribuție SRL | factură furnizor | Laptop 14" | 5 | 14.500,00 lei |
| 12.05.2026 | Nord Computers SRL | factură furnizor | Laptop 14" | 4 | 11.200,00 lei |
| 20.05.2026 | Nord Computers SRL | notă de credit furnizor (retur) | Laptop 14" | 1 | 2.800,00 lei |

Ținta Nord Computers SRL 2026, în valoare:

| Trimestru | Categorie | Țintă |
|---|---|---|
| T1 | (globală) | 30.000,00 |
| T2 | (globală) | 30.000,00 |
| T1 | Laptopuri | 25.000,00 |
| T1 | Accesorii | 2.000,00 |

## 5. Configurare inițială

1. Instalați modulul **Purchase Targets by Manufacturer** din **Aplicații**. Scoateți filtrul
   **Aplicații** din căutare, pentru că modulul nu e o aplicație. Se instalează împreună cu
   *Products Extension*, *Sale Margin* și *eCommerce*, dacă nu erau deja instalate.
2. Pe fiecare producător cu țintă, în **Contacte**, bifați **Este producător** (fișa
   *Products Extension*).
3. Pe produse completați **Producător** și **Categorii eCommerce** (fila **Vânzări**). Pentru
   mii de produse folosiți exportul și importul din listă.
4. Verificați că utilizatorii au drepturile din secțiunea 3.

## 6. Flux de utilizare

### Pasul 1 — Producătorul și categoria pe produs

Deschideți **Achiziții → Produse → Produse** și alegeți **Laptop 14"**. Verificați:
- câmpul **Producător** este **Nord Computers SRL**;
- în fila **Vânzări**, **Categorii eCommerce** conține **Laptopuri**.

Un produs poate avea mai multe categorii eCommerce: **Docking USB-C** este și în **Laptopuri**, și în
**Accesorii / Docking**.

Fără producător completat, produsul nu intră în nicio țintă. Fără categorie, intră doar în ținta
globală a producătorului.

![Produsul Laptop 14" cu producătorul Nord Computers SRL și categoria eCommerce Laptopuri](../static/description/01_produs_producator_categorii.png)

### Pasul 2 — Definirea țintei producătorului

Deschideți **Achiziții → Produse → Ținte producători** și apăsați **Nou**. Completați:
- **Producător:** Nord Computers SRL;
- **An:** 2026;
- **Tip țintă:** **Valoare** (achiziții fără TVA, în lei) sau **Cantitate** (bucăți, în unitatea de
  măsură a fiecărui produs).

Câmpul **Furnizori** se completează singur cu producătorul. Doar facturile acestor parteneri intră
în realizat, deci facturile redistribuitorilor (IT Distribuție SRL) nu se numără. Dacă producătorul
facturează și prin altă firmă din grupul lui, adăugați-o aici.

În fila **Ținte** adăugați câte o linie pe trimestru:
- fără **Categorie**, pentru ținta globală a producătorului;
- cu o **Categorie**, pentru ținta acelei categorii (subcategoriile ei sunt incluse).

Pe demo: T1 și T2 globale de 30.000,00 lei, T1 **Laptopuri** 25.000,00 lei și T1 **Accesorii**
2.000,00 lei. Salvați.

Coloanele **Țintă cumulată**, **Achiziționat cumulat**, **Realizat %** și **Rămas** se calculează
imediat în formular.

![Ținta Nord Computers SRL 2026, cu liniile pe trimestre și categorii și realizatul calculat](../static/description/02_tinta_producator.png)

### Pasul 3 — Realizat vs. țintă

Deschideți **Achiziții → Raportare → Realizat vs. țintă** sau apăsați butonul **Realizat** din
formularul țintei. Lista se deschide pe anul curent, grupată pe producător. Rândurile sub țintă
sunt roșii, iar cele cu ținta atinsă sunt verzi.

1. **Găsiți pe ecran** — pentru fiecare linie de țintă (trimestru × categorie):
   - **Țintă** și **Țintă cumulată** (suma țintelor de la T1 până la trimestrul liniei);
   - **Achiziționat** în trimestru și **Achiziționat cumulat**;
   - **Realizat %** și **Rămas**;
   - **Vândut** în trimestru și **Vândut cumulat**.

   Coloanele cu cantități (**Cantitate achiziționată**, **Cantitate vândută**) se afișează din
   meniul de coloane opționale.
2. **Verificați** pe demo:
   - **T1 global**: achiziționat 28.000,00 + 1.500,00 = **29.500,00**, din ținta de 30.000,00, adică
     **98,33 %** și 500,00 rămas. Factura de 14.500,00 a redistribuitorului nu e inclusă.
   - **T2 global**: în trimestru 11.200,00 − 2.800,00 (retur) = **8.400,00**; cumulat
     29.500,00 + 8.400,00 = **37.900,00** din ținta cumulată de **60.000,00**, adică **63,17 %** și
     22.100,00 rămas.
   - **T1 Laptopuri**: **29.500,00** (laptopurile plus docking-ul, care e și în Laptopuri) din
     25.000,00, adică **118 %**, verde.
   - **T1 Accesorii**: doar docking-ul, din subcategoria **Accesorii / Docking**: **1.500,00** din
     2.000,00, adică **75 %**.
   - **Vândut** pe T1 global: **10.500,00** (3 laptopuri facturate clientului).
   - Docking-ul se numără în ambele categorii, dar o singură dată în ținta globală. Suma
     categoriilor poate depăși deci totalul global.
3. **Treceți mai departe** — selectați rândurile și folosiți **Acțiuni → Exportă** pentru Excel.
   Pe fiecare rând, iconițele din dreapta deschid documentele din spatele cifrelor (pașii 4 și 5).

![Realizat vs. țintă pentru Nord Computers SRL, cu T1 global la 98,33 % și T2 cumulat la 63,17 %](../static/description/03_realizat_vs_tinta.png)

### Pasul 4 — Facturile din spatele realizatului

Pe rândul **T2 global**, apăsați iconița coș (**Linii facturi furnizor**). Se deschid liniile de
factură ale trimestrului care formează cifra.

1. **Găsiți pe ecran** — liniile facturii din 12.05.2026 (Laptop 14", 11.200,00) și ale notei de
   credit din 20.05.2026 (2.800,00, cu minus).
2. **Verificați** că suma liniilor este **8.400,00**, egală cu **Achiziționat** din pasul 3, și că
   nu apare nicio linie a redistribuitorului.
3. **Treceți mai departe** — înapoi la raport din bara de navigare (breadcrumb).

![Liniile facturilor furnizor din T2 pentru ținta Nord Computers SRL: factura și returul](../static/description/04_linii_facturi_furnizor.png)

### Pasul 5 — Vânzările pe aceleași produse

Pe rândul **T1 global**, apăsați iconița grafic (**Vânzări**). Iconița e vizibilă doar
utilizatorilor cu drept pe raportul de profit. Se deschide **Raport analiză profit**, filtrat pe
produsele producătorului și pe trimestru.

1. **Găsiți pe ecran** — factura client din 15.02.2026: 3 × Laptop 14", **Valoare vânzare**
   10.500,00, cu costul și profitul.
2. **Verificați** că **Valoare vânzare** totală este egală cu **Vândut** din pasul 3. Vânzările
   produselor cumpărate prin redistribuitori se numără și ele, pentru că filtrul este pe producător,
   nu pe furnizor.
3. **Treceți mai departe** — comparați cumpărat cu vândut. O achiziție mult peste vânzare înseamnă
   stoc care trebuie susținut cu campanii, iar o vânzare peste achiziție arată unde se poate
   completa achiziția ca să se atingă ținta.

![Raport analiză profit cu vânzările Laptop 14" din T1, deschis din ținta producătorului](../static/description/05_vanzari_aceleasi_produse.png)

### Pasul 6 — Comparația costului între furnizori

Deschideți **Achiziții → Raportare → Comparație cost furnizori**. Analiza facturilor furnizor se
deschide ca pivot: produsele pe rânduri, furnizorii pe coloane, măsura **Preț mediu**.

1. **Găsiți pe ecran** — rândul **Laptop 14"**: **2.800,00** la Nord Computers SRL și **2.900,00**
   la IT Distribuție SRL.
2. **Verificați** perioada din filtrul de dată și că sunt bifate filtrele **Furnizori** și
   **Facturat** (implicite). Prețul este media ponderată din facturi, fără TVA, nu prețul din lista
   de prețuri a furnizorului.
3. **Treceți mai departe** — butonul de descărcare al pivotului exportă tabelul în Excel. Pentru
   comparația pe o comandă în lucru, butonul **Compare supplier prices** al modulului
   *deltatech_purchase_price_compare*, dacă e instalat, folosește prețurile din listele furnizorilor.

![Comparație cost furnizori: Laptop 14" la 2.800,00 lei de la producător și 2.900,00 lei de la redistribuitor](../static/description/06_comparatie_cost_furnizori.png)

### Pasul 7 — Producătorul în Analiza achizițiilor

Deschideți **Achiziții → Raportare → Achiziții** (analiza comenzilor de achiziție). În
**Grupează după** apare **Producător**, iar în căutare se poate tasta numele producătorului.

1. **Găsiți pe ecran** — valorile comandate pe producător.
2. **Verificați** — aici sunt **comenzile**, nu facturile. Diferența față de realizatul din pasul 3
   înseamnă comenzi încă nefacturate. Ținta se urmărește doar pe facturi.

![Analiza achizițiilor grupată pe producător](../static/description/07_analiza_achizitii_producator.png)

### Note de monografie și raportare

Modulul nu generează note contabile și nu modifică facturile, comenzile sau costurile.

- **Realizatul** este suma liniilor de produs din facturile de furnizor postate, minus notele de
  credit de la furnizor. Valoarea este fără TVA, în moneda companiei, la data contabilă a facturii.
  Transportul și discounturile globale fără producător nu intră.
- **Cifrele nu se memorează**, ci se recalculează la fiecare deschidere. O factură postată sau
  anulată schimbă imediat realizatul, inclusiv pe trimestrele trecute.
- **Producătorul și categoriile sunt cele actuale ale produsului**: dacă le schimbați, se schimbă
  și realizatul perioadelor trecute. Pentru un trimestru închis, păstrați exportul.
- **Ținta în cantitate** adună cantitățile în unitatea de măsură a fiecărui produs. Folosiți-o
  doar pentru producători cu produse în aceeași unitate (bucăți).
- **Bonusul de volum** primit de la producător după atingerea țintei se înregistrează, ca orice
  reducere comercială primită, pe factura sau nota de credit a furnizorului. Ca notă de credit de
  la același furnizor, scade realizatul.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `purchase` | meniurile **Achiziții**, analiza comenzilor | dependență (manifest) |
| `deltatech_product_extension` | **Producător** pe produs, **Este producător** pe partener, producătorul în analiza facturilor | dependență (manifest) |
| `website_sale` | **Categorii eCommerce** pe produs | dependență (manifest) |
| `deltatech_sale_margin` | **Raport analiză profit**, sursa vânzărilor | dependență (manifest) |
| `deltatech_sale_margin_pos` | bonurile POS nefacturate în vânzări | opțional |
| `deltatech_purchase_price_compare` | comparația de preț pe comanda în lucru | opțional, complementar |

**Ce e automat:**
- furnizorul implicit al țintei (producătorul);
- realizatul, procentul, ce a rămas și vânzările, recalculate la fiecare deschidere;
- includerea subcategoriilor în ținta unei categorii;
- excluderea facturilor altor furnizori decât cei ai țintei.

**Ce rămâne manual:**
- marcarea producătorilor și completarea producătorului și a categoriilor eCommerce pe produse;
- introducerea țintelor la începutul anului, din contractele cu producătorii;
- adăugarea altor firme ale producătorului în **Furnizori**;
- înregistrarea bonusului de volum.

## 8. Verificări pentru consultant

- [ ] Producătorii cu ținte au bifa **Este producător**, iar produsele lor au **Producător** și
      **Categorii eCommerce** completate.
- [ ] O țintă nouă primește singură furnizorul (producătorul) în **Furnizori**.
- [ ] O a doua linie cu același trimestru și aceeași categorie este refuzată.
- [ ] O a doua țintă pentru același producător și an este refuzată.
- [ ] Pe demo, T1 global arată 29.500,00 achiziționat și 98,33 %, iar T2 global 37.900,00 cumulat
      și 63,17 %.
- [ ] Factura redistribuitorului (14.500,00) nu apare în realizat și nici în liniile din pasul 4.
- [ ] Returul de 2.800,00 scade realizatul din T2.
- [ ] Ținta pe **Accesorii** include docking-ul din subcategoria **Accesorii / Docking**.
- [ ] **Vândut** pe T1 este egal cu totalul din **Raport analiză profit** deschis din rând.
- [ ] **Comparație cost furnizori** arată Laptop 14" la 2.800,00 (Nord Computers) și 2.900,00
      (IT Distribuție).
- [ ] Un achizitor simplu vede țintele doar în citire și nu vede meniul **Raportare**.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|---|---|---|
| „Există deja o țintă pentru acest producător și an.” | Ținta anului există, poate arhivată | Deschideți ținta existentă (filtrul **Arhivat** pentru cele arhivate) și completați-o |
| „Categoria are deja o țintă în trimestrul T…” | Două linii cu același trimestru și aceeași categorie (sau ambele globale) | Păstrați o singură linie și corectați valoarea |
| Realizatul este 0 | Producătorul nu e completat pe produse sau factura e de la alt partener decât cel din **Furnizori** | Completați producătorul; adăugați firma care facturează în **Furnizori** |
| Realizatul pe categorie este 0, dar cel global nu | Produsele nu au categoria eCommerce a liniei | Completați **Categorii eCommerce** pe produse |
| Suma categoriilor depășește totalul global | Produse în mai multe categorii | Normal: se numără în fiecare categorie, o singură dată global |
| Lipsește meniul **Realizat vs. țintă** | Utilizatorul nu e **Achiziții / Administrator** | Butonul **Realizat** din formularul țintei, sau dreptul de administrator |
| Lipsește iconița **Vânzări** pe rând | Utilizatorul nu are drept pe raportul de profit | Dreptul de raport de marjă sau **Vânzări / Administrator** |
| Realizatul unui trimestru închis s-a schimbat | Factură postată sau anulată ulterior, ori producătorul sau categoria produsului au fost schimbate | Cifrele sunt live; păstrați exportul pentru perioadele închise |

## 10. Capturi de ecran

Capturile (`static/description/`) **nu sunt încă generate**: trebuie rulat skill-ul
`fisa-screenshots`. Se generează din `tests/test_screenshots.py`, cu mixinul `ScreenshotCase` din
`l10n_ro_doc_screenshots` (import defensiv), în **limba română**, pe compania **Demo Distribuție
SRL**, cu planul de conturi RO și datele din secțiunea 4.

| # | Fișier | Conținut |
|---|---|---|
| 1 | `01_produs_producator_categorii.png` | formularul produsului Laptop 14" cu **Producător** și **Categorii eCommerce** |
| 2 | `02_tinta_producator.png` | formularul țintei Nord Computers SRL 2026 cu liniile pe trimestre și categorii |
| 3 | `03_realizat_vs_tinta.png` | lista **Realizat vs. țintă** grupată pe producător |
| 4 | `04_linii_facturi_furnizor.png` | liniile facturilor furnizor din T2 (factura și returul) |
| 5 | `05_vanzari_aceleasi_produse.png` | **Raport analiză profit** deschis din rândul T1 |
| 6 | `06_comparatie_cost_furnizori.png` | pivotul **Comparație cost furnizori** produs × furnizor |
| 7 | `07_analiza_achizitii_producator.png` | **Analiza achizițiilor** grupată pe producător |

Regenerare:

```bash
./odoo/odoo-bin -c odoo.conf -d <db> -i l10n_ro,l10n_ro_doc_screenshots,deltatech_purchase_target \
    --test-tags=fise_screenshots/deltatech_purchase_target --stop-after-init \
    --http-port=8987 --gevent-port=8988
```

## 11. Observații pentru manual

Prezentați modulul în capitolul de achiziții, după nomenclatorul de produse. Ordinea de lucru:
1. producătorii marcați, apoi producătorul și categoriile eCommerce completate pe produse;
2. ținta pe an, introdusă din contract, cu trimestrele și categoriile;
3. urmărirea lunară în **Realizat vs. țintă**, cu verificarea pe facturi și pe vânzări;
4. la final de trimestru, exportul raportului pentru arhivă și pentru discuția cu producătorul.

### Limitări cunoscute

- **Doar facturile contează:** comenzile și recepțiile nefacturate nu intră în realizat.
- **Cifre live, nememorate:** schimbarea producătorului sau a categoriilor pe produs ori facturile
  postate retroactiv modifică trimestrele trecute.
- **Produse în mai multe categorii:** se numără în fiecare categorie.
- **Ținta în cantitate** nu convertește unitățile de măsură între produse.
- **Un singur tip de țintă pe an:** valoare sau cantitate. Pentru un producător cu ambele tipuri
  de țintă, tipul se alege pe țintă, nu pe linie.
- **Lista Realizat vs. țintă** nu afișează totaluri pe grup pentru coloanele de realizat, pentru că
  sunt calculate live. Totalul pe producător îl dă linia globală (fără categorie).
