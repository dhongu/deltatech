# Fișă Modul: Disponibilitate în stoc și termen de livrare în magazin

**Modul:** `deltatech_website_stock_availability`
**Utilizator principal:** Administrator website, responsabil vânzări online, achizitor
**Prioritate:** 🟡 Medie (influențează direct decizia de cumpărare și promisiunea de livrare; fără impact contabil)

---

## 1. Scop business

Clientul unui magazin online vrea să știe două lucruri înainte să comande: dacă produsul e pe stoc
și când îl primește. Modulul afișează pe pagina produsului disponibilitatea („În stoc”, „În stoc la
furnizor”, „Nu este în stoc”) și un termen de livrare estimat („Livrare mâine”, „Livrare în 2 - 3
zile”, „Livrare în 3 săptămâni”), calculat din termenul de livrare al produsului, zilele de
siguranță și, pentru produsele care nu sunt pe stoc, termenul și stocul primului furnizor. Clientul
poate comanda și când stocul propriu nu ajunge. Pe cardurile din lista de produse, statusul
„Livrare imediată” / „Livrare ulterioară” se configurează din editorul website-ului, iar în coș
fiecare linie arată dacă se livrează imediat sau ulterior.

## 2. Bază legală și context

Nu există o obligație legală specifică modulului. Contextul este cel de informare corectă a
cumpărătorului înainte de comandă: termenul de livrare afișat este o estimare, nu un angajament
contractual, și trebuie să corespundă cu termenele comunicate în condițiile de vânzare ale
magazinului. Dacă termenele furnizorilor nu sunt întreținute, estimarea devine nerealistă.

## 3. Utilizatori și roluri

- **Responsabil vânzări / catalog** — completează pe produs termenul de livrare, zilele de siguranță
  și opțiunile de stoc pentru eCommerce.
- **Achizitor** — întreține pe liniile de furnizor termenul de livrare, cantitatea disponibilă la
  furnizor și data de început a ofertei.
- **Designer / Administrator website** — configurează statusul stocului pe cardurile din magazin și
  activează sau oprește mesajele opționale.
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
- **Produs A**, stocabil, cu 10 bucăți în stoc, **Delivery Time** 2 zile, timp de siguranță 1 zi;
- **Produs B**, stocabil, fără stoc propriu, cu un furnizor care are **Quantity Available** 50 și
  **Lead Time** 3 zile;
- **Produs C**, stocabil, fără stoc propriu și fără stoc la furnizor;
- toate produsele publicate, cu **Sell when Out-of-Stock** bifat, ca să poată fi comandate.

## 5. Configurare inițială

1. Instalați modulul `deltatech_website_stock_availability`. Se instalează și `website_sale_stock`,
   `purchase` și `deltatech_vendor_stock` (cantitatea disponibilă la furnizor).
2. Pe produs, tab-ul **Inventar**, grupul **Logistics**: completați **Delivery Time** (termenul de
   livrare către client, în zile) și, sub el, **Customer Safety Lead Time** (zilele de siguranță
   adăugate la capătul intervalului).
3. Pe produs, tab-ul **eCommerce**, grupul **Inventory**: bifați **Sell when Out-of-Stock** dacă
   produsul se poate comanda fără stoc și, opțional, **Hide "Out of stock" message**, pentru
   produsele la care nu vreți să apară mesajul „Nu este în stoc”.
4. Pe produs, tab-ul **Achiziție**, pe **prima** linie de furnizor: **Lead Time** (zile, cu
   zecimale), **Quantity Available** (stocul furnizorului) și, dacă oferta începe mai târziu, data
   de început. Modulul ia în calcul doar prima linie de furnizor.

## 6. Flux de utilizare

### Pasul 1 — Produs pe stoc: disponibilitate și termen de livrare

Vizitatorul deschide pagina **Produsului A** (10 bucăți libere în stoc). Sub zona de adăugare în
coș apar:
- mesajul verde **În stoc**;
- termenul de livrare, după **Delivery Time** al produsului:
  - 0 zile → **Livrare imediată**;
  - 1 zi → **Livrare mâine**;
  - 2–7 zile → **Livrare în** 2 - 3 **zile** (de la termenul produsului la termen + zilele de
    siguranță);
  - peste 7 zile → **Livrare în** N **săptămâni** (termenul împărțit la 7, rotunjit).

Stocul luat în calcul este cel liber (disponibil, nerezervat), nu cel faptic.

### Pasul 2 — Produs fără stoc, disponibil la furnizor

Vizitatorul deschide pagina **Produsului B** (fără stoc propriu, 50 bucăți la furnizor, termen 3
zile). Apar:
- mesajul portocaliu **În stoc la furnizor**;
- termenul de livrare, din **Delivery Time** al produsului + **Lead Time** al primului furnizor:
  **Livrare în** 5 - 6 **zile** pentru un termen de produs de 2 zile (2 + 3 până la 2 + 1 + 3);
  peste 7 zile, termenul se afișează în săptămâni; un termen de furnizor sub o zi (de ex. 0,5)
  afișează **Livrare imediată**.

Dacă oferta furnizorului începe la o dată viitoare, zilele rămase până atunci se adaugă la
termenul furnizorului.

### Pasul 3 — Produs fără stoc nicăieri

Pagina **Produsului C** (fără stoc propriu și fără stoc la furnizor) arată mesajul roșu **Nu este în
stoc** și **Timp de livrare necunoscut**. Dacă pe produs e bifat **Hide "Out of stock" message**,
mesajul roșu nu apare; termenul „necunoscut” rămâne. Comanda este posibilă dacă produsul are
**Sell when Out-of-Stock** bifat.

**Ce verificați pe ecran (pașii 1–3):**
- la schimbarea variantei (culoare, mărime), mesajele se recalculează pentru varianta aleasă;
- termenele corespund calculului de mai sus, cu datele din produs și din prima linie de furnizor;
- mesajele apar în limba site-ului (traducerile modulului sunt încărcate în magazin).

### Pasul 4 — Statusul stocului pe cardurile din magazin

Ca designer, deschideți magazinul (`/shop`), apăsați **Editare** și selectați lista de produse. În
panoul din dreapta, secțiunea **Products Design**, sub **Ratings** (Evaluări), apare rândul **Stock
Status** (Status stoc):
- **Ascuns** (implicit), **Text**, **LED** sau **LED cu text**;
- dacă statusul nu e ascuns: **Poziție** — **Deasupra prețului**, **Pe imagine** (stânga jos), **Pe
  imagine, stânga sus** sau **Lângă preț**;
- **Culoare fără stoc** — **Portocaliu**, **Gri** sau **Roșu**.

Salvați. Fiecare card arată **Livrare imediată** (verde) pentru produsele cu stoc faptic pozitiv și
**Livrare ulterioară** (în culoarea aleasă) pentru celelalte. Pe imagine, stânga sus, statusul se
mută ca să nu acopere eticheta (ribbon) din stânga sau insigna „Nepublicat”.

**Ce verificați pe ecran:**
- pe cardurile produselor A și B/C apar statusuri diferite;
- statusul apare în poziția aleasă; designerul îl vede în editor ca să-l poată configura;
- website-urile care aveau activ vechiul badge „Product Available” pe card îl păstrează, ca text
  deasupra prețului.

### Pasul 5 — Coșul de cumpărături

Vizitatorul adaugă produsele în coș și deschide coșul. Sub denumirea fiecărei linii apare:
- **Livrare imediată** (verde), când stocul liber acoperă cantitatea comandată;
- cantitatea disponibilă + **Livrare imediată** + **Livrare ulterioară**, când stocul acoperă doar o
  parte;
- **Livrare ulterioară** (galben), când nu există stoc liber.

Opțional, aceleași badge-uri pot apărea și în rezumatul comenzii din pașii de finalizare (checkout),
prin vizualizarea **Delivery Lead Time** de pe `checkout_layout`, oprită după instalare; acolo se
compară cantitatea comandată cu stocul faptic.

### Pasul 6 — Activarea sau oprirea mesajelor de pe pagini

Mesajele sunt vizualizări opționale ale paginilor magazinului:
- **Product Available** — disponibilitatea pe pagina produsului (activă);
- **Delivery Lead Time** — sunt trei vizualizări cu acest nume: termenul de livrare pe pagina
  produsului (activă), badge-urile din coș (activă) și cele din rezumatul de checkout (oprită).

În Odoo 20 ele nu au comutator în panoul editorului, așa că se activează sau se opresc din
vizualizări: cu modul de dezvoltare activ, **Setări → Tehnic → Interfață utilizator →
Vizualizări**, căutați după nume, deschideți vizualizarea și bifați sau debifați **Activ**.

### Note de monografie și raportare

Modulul nu generează note contabile și nu are rapoarte. Nu rezervă stoc și nu creează comenzi de
achiziție: doar afișează informații calculate din stocul curent și din datele furnizorului.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `website_sale_stock` | stocul pe website, opțiunea **Sell when Out-of-Stock**, pagina produsului și coșul | dependență (manifest) |
| `purchase` | liniile de furnizor de pe produs (termen, dată de început) | dependență (manifest) |
| `deltatech_vendor_stock` | câmpul **Quantity Available** pe linia de furnizor (stocul furnizorului) | dependență (manifest) |
| `website` | editorul (panoul **Products Design**) și traducerile din magazin | dependență (manifest) |
| Recepții și livrări din Inventar | modifică stocul liber pe care se bazează mesajele | indirect |

Ce este automat: calculul disponibilității și al termenului pe pagina produsului, la fiecare
schimbare de variantă; statusul de pe carduri; badge-urile din coș.
Ce rămâne manual: întreținerea termenelor pe produse, a stocului și a termenelor la furnizori
(eventual prin importul stocului furnizorului); alegerea stilului din editor.

## 8. Verificări pentru consultant

- [ ] Produs cu stoc liber: **În stoc** și termenul după **Delivery Time** (0 → imediat, 1 → mâine,
  2–7 → interval în zile, peste 7 → săptămâni).
- [ ] Capătul intervalului = **Delivery Time** + **Customer Safety Lead Time**.
- [ ] Produs fără stoc, cu stoc la primul furnizor: **În stoc la furnizor** și termenul include
  **Lead Time** al furnizorului.
- [ ] O dată de început viitoare pe linia furnizorului mărește termenul cu zilele rămase.
- [ ] Produs fără stoc nicăieri: **Nu este în stoc** și **Timp de livrare necunoscut**; cu **Hide
  "Out of stock" message** bifat, mesajul roșu dispare.
- [ ] La schimbarea variantei, mesajele se actualizează.
- [ ] **Stock Status** din **Products Design** afișează statusul în poziția și culoarea alese.
- [ ] În coș, liniile acoperite de stoc au **Livrare imediată**, celelalte **Livrare ulterioară**.
- [ ] Filtrul `?ppg=` din adresa magazinului nu mai filtrează produsele după preț.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| Pe pagina produsului nu apare niciun mesaj de stoc | produsul nu este stocabil, sau vizualizările **Product Available** / **Delivery Lead Time** sunt oprite | marcați produsul ca stocabil; verificați vizualizările |
| **Timp de livrare necunoscut** la un produs care se găsește la furnizor | stocul furnizorului (**Quantity Available**) sau termenul (**Lead Time**) lipsesc pe **prima** linie de furnizor | completați prima linie de furnizor sau mutați furnizorul principal pe primul loc |
| Cardul arată **Livrare imediată**, iar pagina produsului arată „Nu este în stoc” | cardul folosește stocul faptic, pagina produsului stocul liber; produsul are tot stocul rezervat | comportament actual; verificați rezervările |
| Badge-ul din coș diferă de cel din rezumatul checkout-ului | coșul compară cu stocul liber, rezumatul checkout cu stocul faptic | comportament actual; țineți activă doar una dintre vizualizări dacă diferența derutează clienții |
| „Livrare în NaN săptămâni” | versiune veche a modulului, cu termen de produs peste 7 zile | actualizați modulul (corectat în 20.0.1.0.10) |
| Lista din magazin pierde produsele ieftine când adresa conține `?ppg=40` | versiune veche a modulului, care trimitea `ppg` ca preț minim | actualizați modulul (corectat în 19.0.1.0.9) |

## 10. Capturi de ecran

Fișa este, deocamdată, doar text: nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele
în cuvinte. Când se vor adăuga capturi, se generează cu skill-ul `fisa-screenshots` (mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, în română), câte una pentru fiecare pas.

## 11. Observații pentru manual

Explicați că termenul afișat este o estimare calculată din date: dacă termenele produselor și ale
furnizorilor nu sunt întreținute, promisiunea de livrare devine greșită. Subliniați că modulul
folosește doar prima linie de furnizor și că pagina produsului și coșul lucrează cu stocul liber,
iar cardurile din magazin cu stocul faptic. Recomandați clientului un stil de status pe carduri
(text sau LED) consecvent cu restul site-ului.
