# Fișă Modul: Prețul fără TVA pe pagina produsului din magazin

**Modul:** `deltatech_website_price_without_tax`
**Utilizator principal:** Administrator website, responsabil magazin online
**Prioritate:** 🟡 Medie (util pentru magazinele cu clienți firme; nu generează documente contabile)

---

## 1. Scop business

Un magazin online care vinde și persoanelor fizice, și firmelor afișează de obicei prețul cu TVA,
pentru că acesta e prețul final al consumatorului. Clientul firmă calculează însă în prețuri fără
TVA și trebuie să facă singur împărțirea. Modulul adaugă pe pagina produsului, sub preț, rândul
**Preț fără TVA:** cu valoarea netă, calculată din prețul afișat. Merge în ambele sensuri: dacă
site-ul afișează prețurile cu TVA, rândul scoate TVA-ul din ele; dacă le afișează fără TVA, rândul
repetă prețul net.

## 2. Bază legală și context

Pentru vânzarea către consumatori, prețul afișat trebuie să fie prețul final, cu toate taxele
incluse (legislația de protecție a consumatorului privind afișarea prețurilor). Modulul nu schimbă
prețul principal afișat; rândul „Preț fără TVA” este informativ, în plus față de acesta, și nu
înlocuiește prețul cu TVA cerut pentru consumatori. TVA-ul scăzut este cel configurat pe produs
(de ex. 21% sau 11%), după maparea poziției fiscale a clientului.

## 3. Utilizatori și roluri

- **Administrator website** — alege modul de afișare a prețurilor (cu sau fără TVA) și, opțional,
  oprește rândul de pe pagina produsului.
- **Responsabil catalog** — întreține prețurile și taxele de vânzare ale produselor.
- **Vizitatorul magazinului** (public, portal sau intern) — vede rândul **Preț fără TVA:**.

Roluri recomandate pentru testare:
- Administrator cu acces la **Website → Configurare → Setări** și la listele de prețuri.
- O fereastră privată de browser, ca vizitator public.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile și nu creează documente. Nu adaugă câmpuri: calculează
prețul net în momentul afișării paginii.

Date minime pentru demo:
- o taxă de vânzare de 21%, configurată ca „exclusă din preț” (situația obișnuită);
- un produs publicat pe website cu prețul de vânzare 100 lei și taxa de mai sus;
- opțional, un al doilea produs cu o taxă „inclusă în preț” și prețul 121 lei, pentru a verifica
  celălalt caz.

## 5. Configurare inițială

1. Instalați modulul `deltatech_website_price_without_tax` (depinde de `website` și
   `website_sale`). Rândul **Preț fără TVA:** apare imediat pe pagina produselor.
2. Mergeți la **Website → Configurare → Setări** și alegeți la **Display Product Prices** (Afișează
   prețurile produselor) varianta dorită: **Tax Included** (Taxe incluse) sau **Tax Excluded** (Fără
   taxe). Salvați.
3. Dacă folosiți liste de prețuri diferite pentru firme, deschideți lista de prețuri din
   **Website → Produse → Liste de prețuri**, tab-ul **Ecommerce**: câmpul **Price Display**
   suprascrie, pentru acea listă, modul de afișare al website-ului (gol = „Defined on website”).

## 6. Flux de utilizare

### Pasul 1 — Pagina produsului cu prețurile afișate cu TVA

Website-ul afișează prețurile cu TVA (**Tax Included**). Vizitatorul deschide produsul de 100 lei
plus TVA 21%. Prețul principal este 121,00 lei, iar sub el apare rândul **Preț fără TVA:** 100,00 lei.

Prețul net se calculează scăzând din prețul afișat taxele produsului, ca și cum ar fi incluse în
preț, oricum ar fi configurată taxa. Un produs cu taxa „inclusă în preț” și prețul de 121 lei arată
tot 121,00 lei și, sub el, 100,00 lei.

**Ce verificați pe ecran:**
- prețul net este prețul afișat împărțit la (1 + cota TVA): 121 / 1,21 = 100;
- moneda rândului este moneda website-ului;
- valoarea este calculată la încărcarea paginii, pentru varianta afișată inițial; la produsele cu
  variante de prețuri diferite, reîncărcați pagina variantei pentru a verifica rândul.

### Pasul 2 — Pagina produsului cu prețurile afișate fără TVA

Website-ul (sau lista de prețuri a clientului) afișează prețurile fără TVA (**Tax Excluded**).
Prețul principal este deja net, 100,00 lei, iar rândul **Preț fără TVA:** repetă aceeași valoare,
100,00 lei, chiar dacă taxa produsului este „inclusă în preț”.

**Ce verificați pe ecran:**
- rândul **Preț fără TVA:** este egal cu prețul principal;
- pe o listă de prețuri cu **Price Display** = **Taxes Excluded**, rândul este net chiar dacă
  website-ul afișează în rest prețurile cu TVA.

### Pasul 3 — Oprirea rândului pe un website

Rândul este o vizualizare opțională a paginii de produs, numită **Product Price without tax**,
activă după instalare. În Odoo 20 nu are un comutator în panoul editorului de website, așa că se
oprește din vizualizări: cu modul de dezvoltare activ, **Setări → Tehnic → Interfață utilizator →
Vizualizări**, căutați „Product Price without tax”, deschideți vizualizarea și debifați **Activ**.
Dacă website-ul are o copie proprie a vizualizării, opriți copia acelui website: celelalte
website-uri își păstrează opțiunea.

### Note de monografie și raportare

Modulul nu generează note contabile și nu are rapoarte. Prețul fără TVA este doar afișat; comanda,
factura și TVA-ul se calculează în continuare de Odoo, din prețul și taxele produsului.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `website_sale` | pagina produsului, blocul de preț și modul de afișare cu/fără TVA (setare website și listă de prețuri) | dependență (manifest) |
| `account` (taxe) | cotele de TVA ale produsului, din care se scoate prețul net | indirect, prin `website_sale` |
| Liste de prețuri | prețul afișat (cu reducerile aplicate) și, opțional, modul de afișare propriu listei | configurare |

Ce este automat: calculul prețului net la afișarea paginii, respectarea modului de afișare al listei de prețuri.
Ce rămâne manual: alegerea modului de afișare pe website și pe listele de prețuri, întreținerea
taxelor corecte pe produse.

## 8. Verificări pentru consultant

- [ ] Cu prețuri afișate cu TVA, rândul **Preț fără TVA:** = preț afișat / (1 + cota TVA).
- [ ] Cu prețuri afișate fără TVA, rândul este egal cu prețul principal.
- [ ] Rezultatul e același pentru taxă „inclusă în preț” și „exclusă din preț”.
- [ ] Pe o listă de prețuri cu **Price Display** propriu, rândul urmează lista, nu website-ul.
- [ ] Rândul apare atât pentru vizitatorul public, cât și pentru utilizatorul portal.
- [ ] Pe un produs cu reducere din lista de prețuri, comparați rândul cu prețul redus (vezi
  secțiunea 9).
- [ ] Oprirea vizualizării **Product Price without tax** scoate rândul doar pe website-ul ales.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| Rândul nu apare pe pagina produsului | prețul net este zero (produs fără preț) sau vizualizarea **Product Price without tax** este oprită | completați prețul; verificați starea vizualizării pe website |
| Pe un produs cu reducere, „Preț fără TVA” este mai mare decât prețul redus fără TVA | rândul este calculat din prețul de dinainte de reducere (cel tăiat), nu din prețul redus | semnalat ca bug ([#3822](https://github.com/dhongu/deltatech/issues/3822)); până la corectare, verificați produsele cu reduceri |
| Pe site-ul în engleză, eticheta apare tot „Preț fără TVA:” | eticheta este scrisă în română direct în șablon | semnalat ca bug ([#3822](https://github.com/dhongu/deltatech/issues/3822)); pe site-urile în română eticheta e corectă |
| Prețul net este greșit (121 afișat ca net sau 82,64 în loc de 100) | versiune veche a modulului, când afișarea website-ului și setarea taxei erau diferite | actualizați modulul (corectat în 19.0.1.0.6) |
| La actualizarea din 18.0 apare eroarea „Element `<xpath expr="//div[@itemprop='offers']">` cannot be located in parent view” | vizualizarea veche din 18.0 rămasă în bază | actualizați modulul la o versiune de la 19.0.1.0.4 încolo, care conține scriptul de migrare |

## 10. Capturi de ecran

Fișa este, deocamdată, doar text: nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele
în cuvinte. Când se vor adăuga capturi, se generează cu skill-ul `fisa-screenshots` (mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, în română), câte una pentru fiecare pas.

## 11. Observații pentru manual

Subliniați că rândul „Preț fără TVA” este informativ: prețul principal, comanda și factura nu se
schimbă. Explicați că valoarea urmează modul de afișare a prețurilor, care poate fi diferit pe
listele de prețuri pentru firme. La produsele cu reduceri, verificați valoarea până la corectarea
calculului (secțiunea 9).
