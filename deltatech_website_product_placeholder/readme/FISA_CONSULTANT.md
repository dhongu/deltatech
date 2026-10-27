# Fișă Modul: Imagine implicită pentru produsele fără poză

**Modul:** `deltatech_website_product_placeholder`
**Utilizator principal:** Administrator website
**Prioritate:** 🟢 Scăzută (îmbunătățire de prezentare și viteză a site-ului, fără impact contabil)

---

## 1. Scop business

Un catalog mare are aproape întotdeauna produse fără fotografie. Odoo le afișează cu o imagine
generică și o servește separat pentru fiecare produs, ceea ce încarcă serverul și nu se păstrează
bine în cache-ul browserului sau al CDN-ului. Modulul permite alegerea unei imagini proprii pentru
produsele fără poză, pe fiecare website (de ex. sigla magazinului pe fundal neutru, sau mesajul
„Imagine în curând”), și o servește de la o singură adresă pentru toate aceste produse. Pagina se
încarcă mai repede, iar magazinul arată unitar.

## 2. Bază legală și context

Nu există o obligație legală. Contextul este cel de prezentare și performanță a site-ului: o
singură adresă de imagine pentru toate produsele fără poză se descarcă o dată și se refolosește din
cache. Imaginea aleasă nu trebuie să sugereze că reprezintă produsul (de ex. o fotografie a altui
produs), ca să nu inducă în eroare cumpărătorul.

## 3. Utilizatori și roluri

- **Administrator website** — încarcă imaginea implicită în setările website-ului.
- **Responsabil catalog** — vede pe site care produse încă nu au fotografie.
- **Vizitatorul magazinului** — vede imaginea implicită în locul pozei lipsă.

Roluri recomandate pentru testare:
- Administrator cu acces la **Website → Configurare → Setări**.
- O fereastră privată de browser, ca vizitator public.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile și nu creează documente. Adaugă pe website un singur câmp,
**Product Placeholder Image** (Imagine substituent produs).

Date minime pentru demo:
- un produs publicat pe website, fără imagine;
- un produs publicat, cu imagine (pentru comparație);
- o imagine pătrată (PNG sau JPG), de ex. sigla magazinului pe fundal alb.

## 5. Configurare inițială

1. Instalați modulul `deltatech_website_product_placeholder` (depinde de `website_sale`). Fără altă
   configurare, produsele fără poză primesc imediat imaginea implicită a modulului, în locul celei
   generice din Odoo.
2. Dacă aveți mai multe website-uri, alegeți în setări website-ul pe care îl configurați: imaginea
   se ține separat pe fiecare website.

## 6. Flux de utilizare

### Pasul 1 — Încărcarea imaginii implicite pe website

Mergeți la **Website → Configurare → Setări**. În blocul **General**, la setarea **Substituent
produs** (Product Placeholder, cu explicația „Default image used for products without an image”),
încărcați imaginea dorită și salvați.

Fără imagine încărcată, modulul folosește imaginea proprie inclusă în el. Pentru a reveni la
aceasta, ștergeți imaginea din setare și salvați.

### Pasul 2 — Produsele fără poză în magazin

Deschideți magazinul (`/shop`) ca vizitator. Produsele fără imagine afișează imaginea încărcată la
pasul 1, atât în lista de produse, cât și pe pagina produsului, în orice mărime (miniatură, card,
imagine mare). Produsele care au poză își păstrează poza.

**Ce verificați pe ecran:**
- toate produsele fără poză arată aceeași imagine, cea din setări;
- produsele cu poză nu sunt afectate;
- pe un al doilea website fără imagine încărcată apare imaginea implicită a modulului, nu cea a
  primului website;
- din inspectorul browserului, imaginea produselor fără poză are aceeași adresă pentru toate
  produsele (`/web/image/website/<id website>/product_placeholder_image`), nu una per produs.

### Note de monografie și raportare

Modulul nu generează note contabile și nu are rapoarte. Nu modifică produsele: nu le atribuie
imaginea implicită, doar o afișează în locul pozei lipsă.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `website_sale` | magazinul, cardurile și pagina produsului, unde apare imaginea | dependență (manifest) |
| `website` | setările website-ului (blocul **General**), unde se încarcă imaginea | indirect, prin `website_sale` |

Ce este automat: înlocuirea pozei lipsă în toate mărimile de imagine ale produsului (șablon și
variantă), servirea imaginii de la o adresă unică pe website.
Ce rămâne manual: alegerea și încărcarea imaginii pe fiecare website; adăugarea pozelor reale pe
produse.

## 8. Verificări pentru consultant

- [ ] După instalare, produsele fără poză nu mai arată imaginea generică Odoo, ci imaginea modulului.
- [ ] După încărcarea imaginii în setări, produsele fără poză o afișează în listă și pe pagina
  produsului.
- [ ] Produsele cu poză își păstrează poza.
- [ ] Pe un website fără imagine proprie se folosește imaginea implicită a modulului.
- [ ] Imaginea este vizibilă și pentru vizitatorul neautentificat.
- [ ] Toate produsele fără poză folosesc aceeași adresă de imagine.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| După schimbarea imaginii în setări, site-ul arată tot imaginea veche | imaginea veche este păstrată în cache-ul browserului sau al CDN-ului | goliți cache-ul browserului / purjați CDN-ul |
| Imaginea apare deformată sau tăiată pe carduri | imaginea încărcată nu este pătrată | încărcați o imagine pătrată, cu subiectul centrat |
| Pe un al doilea website apare altă imagine decât cea așteptată | imaginea se ține separat pe fiecare website | selectați website-ul în setări și încărcați imaginea și pentru el |
| În backend (produsele din Vânzări) apare imaginea din setări a unui website | în backend, Odoo ia website-ul curent: cel ales în sesiune, cel al domeniului sau, altfel, primul website | comportament normal; modulul vizează paginile magazinului |

## 10. Capturi de ecran

Fișa este, deocamdată, doar text: nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele
în cuvinte. Când se vor adăuga capturi, se generează cu skill-ul `fisa-screenshots` (mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, în română), câte una pentru fiecare pas.

## 11. Observații pentru manual

Recomandați o imagine discretă, pătrată, care nu poate fi confundată cu un produs. Precizați că
modulul nu înlocuiește fotografiile reale: e o soluție de prezentare pentru produsele care încă nu
au poză. La schimbarea imaginii, amintiți-i clientului de cache-ul browserului și al CDN-ului.
