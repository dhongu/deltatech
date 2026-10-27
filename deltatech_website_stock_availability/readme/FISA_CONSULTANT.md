# Fișă Modul: Disponibilitate în stoc și termen de livrare în magazin

**Modul:** `deltatech_website_stock_availability`
**Utilizator principal:** Administrator website, responsabil vânzări online, achizitor
**Prioritate:** 🟡 Medie (influențează direct decizia de cumpărare și promisiunea de livrare; fără impact contabil)

---

## 1. Scop business

Clientul unui magazin online vrea să știe două lucruri înainte să comande: dacă produsul e pe stoc
și când îl primește. Modulul afișează pe pagina produsului disponibilitatea („În stoc”, „În stoc la
furnizor”, „Nu este în stoc”) și un termen de livrare estimat („Livrare mâine”, „Livrare în 2 - 3
zile”, „Livrare în 3 săptămâni”). Termenul se calculează din termenul de livrare al produsului, din
zilele de siguranță și, pentru produsele care nu sunt pe stoc, din termenul și stocul furnizorului
aplicabil. Clientul poate comanda și când stocul propriu nu ajunge. Pe cardurile din lista de
produse, statusul „Livrare imediată” / „Livrare ulterioară” se configurează din editorul
website-ului, la fel ca stilul insignei de stoc de pe pagina produsului. În coș, fiecare linie arată
dacă se livrează imediat sau ulterior.

## 2. Bază legală și context

Nu există o obligație legală specifică modulului. Contextul este cel de informare corectă a
cumpărătorului înainte de comandă: termenul de livrare afișat este o estimare, nu un angajament
contractual, și trebuie să corespundă cu termenele comunicate în condițiile de vânzare ale
magazinului. Dacă termenele furnizorilor nu sunt întreținute, estimarea devine nerealistă.

## 3. Utilizatori și roluri

- **Responsabil vânzări / catalog** — completează pe produs termenul de livrare, zilele de siguranță
  și opțiunile de stoc pentru eCommerce.
- **Achizitor** — întreține pe liniile de furnizor termenul de livrare, cantitatea disponibilă la
  furnizor și perioada de valabilitate a ofertei.
- **Designer / Administrator website** — configurează statusul stocului pe cardurile din magazin,
  stilul insignei de stoc și mesajele opționale.
- **Vizitatorul magazinului** — vede disponibilitatea și termenul de livrare.

Roluri recomandate pentru testare:
- Administrator cu drepturi de **Designer website** și acces la Inventar și Achiziții.
- O fereastră privată de browser, ca vizitator public.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile și nu creează documente. Adaugă pe produs două câmpuri:
**Customer Safety Lead Time** (Timp de siguranță, implicit 1 zi) și **Hide Out-of-Stock Message**
(Ascunde mesajul „Nu este în stoc”); pe liniile de furnizor, **Lead Time** (termenul de livrare al
furnizorului) acceptă zecimale (de ex. 0,5 zile).

Date minime pentru demo:
- **Produs A**, stocabil, cu 10 bucăți în stoc în depozitul website-ului, **Customer Lead Time** 2
  zile, timp de siguranță 1 zi;
- **Produs B**, stocabil, fără stoc propriu, cu un furnizor activ al companiei website-ului, care
  are **Quantity Available** 50 și **Lead Time** 3 zile;
- **Produs C**, stocabil, fără stoc propriu și fără stoc la furnizor;
- toate produsele publicate, cu **Sell when Out-of-Stock** bifat, ca să poată fi comandate.

## 5. Configurare inițială

1. Instalați modulul `deltatech_website_stock_availability`. Se instalează și `website_sale_stock`,
   `purchase` și `deltatech_vendor_stock` (cantitatea disponibilă la furnizor).
2. Pe produs, tab-ul **Inventar**: în grupul **Logistics** completați **Customer Lead Time**
   (termenul de livrare către client, în zile); în grupul **Operations** completați **Customer
   Safety Lead Time** (zilele de siguranță adăugate la capătul intervalului). Grupul
   **Operations** apare doar când produsul are rute disponibile (de ex. rute de aprovizionare).
3. Pe produs, tab-ul **eCommerce**: bifați **Sell when Out-of-Stock** dacă produsul se poate comanda
   fără stoc și, opțional, **Hide "Out of stock" message**, pentru produsele la care nu vreți să
   apară mesajul „Nu este în stoc”.
4. Pe produs, tab-ul **Achiziție**, pe liniile de furnizor: **Lead Time** (zile, cu zecimale),
   **Quantity Available** (stocul furnizorului) și perioada de valabilitate a ofertei (data de
   început și data de sfârșit).

Furnizorul folosit pe website se alege automat dintre liniile de furnizor ale companiei
website-ului, pentru varianta afișată (sau pentru tot produsul), ale furnizorilor activi și
neexpirate: are prioritate o ofertă valabilă azi; dacă nu există, se ia oferta viitoare cu data de
început cea mai apropiată.

## 6. Flux de utilizare

### Pasul 1 — Produs pe stoc: disponibilitate și termen de livrare

Vizitatorul deschide pagina **Produsului A** (10 bucăți libere în stoc). Sub zona de adăugare în
coș apar:
- mesajul verde **În stoc**;
- termenul de livrare, după **Customer Lead Time** al produsului:
  - 0 zile → **Livrare imediată**;
  - 1 zi → **Livrare mâine**;
  - 2–7 zile → **Livrare în** 2 - 3 **zile** (de la termenul produsului la termen + zilele de
    siguranță);
  - peste 7 zile → apare „Livrare în NaN săptămâni” (bug, vezi secțiunea 9).

Stocul luat în calcul este cel liber (disponibil, nerezervat) al website-ului, nu cel faptic.

### Pasul 2 — Produs fără stoc, disponibil la furnizor

Vizitatorul deschide pagina **Produsului B** (fără stoc propriu, 50 bucăți la furnizor, termen 3
zile). Apar:
- mesajul portocaliu **În stoc la furnizor**;
- termenul de livrare, din **Customer Lead Time** al produsului + **Lead Time** al furnizorului
  aplicabil: **Livrare în** 5 - 6 **zile** pentru un termen de produs de 2 zile (2 + 3 până la
  2 + 1 + 3); peste 7 zile, termenul se afișează în săptămâni; un termen de furnizor sub o zi (de
  ex. 0,5) afișează **Livrare imediată**.

Dacă singura ofertă aplicabilă începe la o dată viitoare, zilele rămase până atunci se adaugă la
termenul furnizorului. Ofertele altei companii, ale altei variante, ale furnizorilor arhivați sau
expirate nu sunt luate în calcul.

### Pasul 3 — Produs fără stoc nicăieri

Pagina **Produsului C** (fără stoc propriu și fără stoc la furnizor) arată mesajul roșu **Nu este în
stoc** și **Timp de livrare necunoscut**. Dacă pe produs e bifat **Hide "Out of stock" message**,
mesajul roșu nu apare; termenul „necunoscut” rămâne. Comanda este posibilă dacă produsul are
**Sell when Out-of-Stock** bifat.

**Ce verificați pe ecran (pașii 1–3):**
- la schimbarea variantei (culoare, mărime), mesajele se recalculează pentru varianta aleasă;
- termenele corespund calculului de mai sus, cu datele din produs și din oferta furnizorului
  aplicabil;
- mesajele apar în limba site-ului (traducerile modulului sunt încărcate în magazin).

### Pasul 4 — Stilul insignei de stoc de pe pagina produsului

Insigna standard de stoc de pe pagina produsului (de ex. „5 Units in stock”, afișată de
`website_sale_stock` când produsul are activată afișarea cantității disponibile) poate primi un
stil propriu. Ca designer, deschideți o pagină de produs, apăsați **Editare** și selectați pagina
produsului. În panoul **Product Page**, rândul **Stock Badge** (Insignă stoc) oferă:
**Pill** (Pastilă, stilul standard), **Text with Dot** (Text cu punct), **Theme Colors** (Culorile
temei), **Outline** (Contur), **Level Bar** (Bară de nivel) și **Status Only** (Doar starea).
Salvați; stilul se aplică tuturor paginilor de produs ale website-ului.

### Pasul 5 — Statusul stocului pe cardurile din magazin

Ca designer, deschideți magazinul (`/shop`), apăsați **Editare** și selectați lista de produse. În
panoul din dreapta, secțiunea **Products Design**, sub **Ratings** (Evaluări), apare rândul **Stock
Status** (Status stoc):
- **Ascuns** (implicit), **Text**, **LED** sau **LED cu text**;
- dacă statusul nu e ascuns: **Poziție** — **Deasupra prețului**, **Pe imagine** sau **Lângă preț**;
- **Culoare fără stoc** — **Portocaliu**, **Gri** sau **Roșu**.

Salvați. Fiecare card arată **Livrare imediată** (verde) pentru produsele cu stoc faptic pozitiv și
**Livrare ulterioară** (în culoarea aleasă) pentru celelalte.

**Ce verificați pe ecran:**
- pe cardurile produselor A și B/C apar statusuri diferite;
- statusul apare în poziția aleasă; designerul îl vede în editor ca să-l poată configura.

### Pasul 6 — Coșul de cumpărături

Vizitatorul adaugă produsele în coș și deschide coșul. Sub denumirea fiecărei linii apare:
- **Livrare imediată** (verde), când stocul liber acoperă cantitatea comandată;
- cantitatea disponibilă + **Livrare imediată** + **Livrare ulterioară**, când stocul acoperă doar o
  parte;
- **Livrare ulterioară** (galben), când nu există stoc liber.

Stocul liber este cel din depozitul comenzii (al website-ului), exprimat în unitatea de măsură a
liniei: stocul din alt depozit nu face linia „imediată”.

Opțional, badge-uri asemănătoare pot apărea și în rezumatul comenzii din pașii de finalizare
(checkout), prin vizualizarea **Delivery Lead Time** de pe `checkout_layout`, oprită după instalare;
acolo se compară cantitatea comandată cu stocul faptic al produsului.

### Pasul 7 — Activarea sau oprirea mesajelor de pe pagini

Mesajele sunt vizualizări opționale ale paginilor magazinului:
- **Product Available** — disponibilitatea pe pagina produsului (activă);
- **Delivery Lead Time** — sunt trei vizualizări cu acest nume: termenul de livrare pe pagina
  produsului (activă), badge-urile din coș (activă) și cele din rezumatul de checkout (oprită).

În Odoo 19 ele nu au comutator în panoul editorului, așa că se activează sau se opresc din
vizualizări: cu modul de dezvoltare activ, **Setări → Tehnic → Interfață utilizator →
Vizualizări**, căutați după nume, deschideți vizualizarea și bifați sau debifați **Activ**.

### Note de monografie și raportare

Modulul nu generează note contabile și nu are rapoarte. Nu rezervă stoc și nu creează comenzi de
achiziție: doar afișează informații calculate din stocul curent și din datele furnizorului.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `website_sale_stock` | stocul pe website, opțiunea **Sell when Out-of-Stock**, insigna de stoc, pagina produsului și coșul | dependență (manifest) |
| `purchase` | liniile de furnizor de pe produs (termen, perioadă de valabilitate) | dependență (manifest) |
| `deltatech_vendor_stock` | câmpul **Quantity Available** pe linia de furnizor (stocul furnizorului) | dependență (manifest) |
| `website` | editorul (panourile **Products Design** și **Product Page**) și traducerile din magazin | dependență (manifest) |
| Recepții și livrări din Inventar | modifică stocul liber pe care se bazează mesajele | indirect |

Ce este automat: alegerea ofertei de furnizor aplicabile, calculul disponibilității și al
termenului pe pagina produsului, la fiecare schimbare de variantă; statusul de pe carduri; badge-urile
din coș, pe depozitul website-ului.
Ce rămâne manual: întreținerea termenelor pe produse, a stocului și a ofertelor furnizorilor
(eventual prin importul stocului furnizorului); alegerea stilurilor din editor.

## 8. Verificări pentru consultant

- [ ] Produs cu stoc liber: **În stoc** și termenul după **Customer Lead Time** (0 → imediat,
  1 → mâine, 2–7 → interval în zile).
- [ ] Capătul intervalului = **Customer Lead Time** + **Customer Safety Lead Time**.
- [ ] Produs fără stoc, cu stoc la furnizor: **În stoc la furnizor** și termenul include **Lead
  Time** al ofertei aplicabile.
- [ ] O ofertă a altei companii, a altei variante, a unui furnizor arhivat sau expirată nu este
  folosită; o ofertă valabilă azi are prioritate față de una viitoare.
- [ ] Produs fără stoc nicăieri: **Nu este în stoc** și **Timp de livrare necunoscut**; cu **Hide
  "Out of stock" message** bifat, mesajul roșu dispare.
- [ ] La schimbarea variantei, mesajele se actualizează.
- [ ] **Stock Badge** din panoul **Product Page** schimbă stilul insignei de stoc.
- [ ] **Stock Status** din **Products Design** afișează statusul în poziția și culoarea alese.
- [ ] În coș, liniile acoperite de stocul depozitului website-ului au **Livrare imediată**,
  celelalte **Livrare ulterioară**; o linie într-o altă unitate de măsură compară corect cantitățile.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| „Livrare în NaN săptămâni” la un produs pe stoc | bug pe 19.0 pentru **Customer Lead Time** peste 7 zile ([#3834](https://github.com/dhongu/deltatech/issues/3834)); corectat pe 20.0 | până la corectare, țineți termenul produselor pe stoc la cel mult 7 zile |
| Pe pagina produsului nu apare niciun mesaj de stoc | produsul nu este stocabil, sau vizualizările **Product Available** / **Delivery Lead Time** sunt oprite | marcați produsul ca stocabil; verificați vizualizările |
| **Timp de livrare necunoscut** la un produs care se găsește la furnizor | oferta furnizorului nu e aplicabilă (altă companie, altă variantă, expirată, furnizor arhivat) sau nu are **Quantity Available** / **Lead Time** | corectați oferta furnizorului |
| Câmpul **Customer Safety Lead Time** nu apare pe produs | grupul **Operations** din tab-ul **Inventar** e ascuns când produsul nu are rute disponibile | activați rutele (de ex. din setările Inventarului) sau completați câmpul prin import |
| Cardul arată **Livrare imediată**, iar pagina produsului arată „Nu este în stoc” | cardul folosește stocul faptic, pagina produsului stocul liber; produsul are tot stocul rezervat | comportament actual; verificați rezervările |
| Badge-ul din coș diferă de cel din rezumatul checkout-ului | coșul compară cu stocul liber al depozitului website-ului, rezumatul checkout cu stocul faptic | comportament actual; țineți activă doar una dintre vizualizări dacă diferența derutează clienții |
| Lista din magazin pierde produsele ieftine când adresa conține `?ppg=40` | versiune veche a modulului, care trimitea `ppg` ca preț minim | actualizați modulul (corectat în 19.0.1.0.9) |

## 10. Capturi de ecran

Fișa este, deocamdată, doar text: nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele
în cuvinte. Când se vor adăuga capturi, se generează cu skill-ul `fisa-screenshots` (mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, în română), câte una pentru fiecare pas.

## 11. Observații pentru manual

Explicați că termenul afișat este o estimare calculată din date: dacă termenele produselor și
ofertele furnizorilor nu sunt întreținute, promisiunea de livrare devine greșită. Subliniați că
pagina produsului și coșul lucrează cu stocul liber al website-ului, iar cardurile din magazin cu
stocul faptic. Recomandați clientului un stil de status pe carduri (text sau LED) și o insignă de
stoc consecvente cu restul site-ului.
