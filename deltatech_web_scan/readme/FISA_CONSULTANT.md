# Fișă Modul: Citirea paginilor web de produs — baza tehnică (Web Scan)

**Modul:** `deltatech_web_scan`
**Utilizator principal:** Consultant / administrator (înțelegerea stărilor citirii și a limitelor), Responsabil achiziții (indirect, prin modulele care îl folosesc)
**Prioritate:** 🟢 Scăzută (bază tehnică fără ecrane proprii; se instalează automat ca dependență și nu generează note contabile)

---

## 1. Scop business

Unii furnizori nu trimit un fișier de prețuri și nu au API, iar prețurile concurenților se văd doar
pe site-urile lor. Modulul este **motorul comun** care citește astfel de **pagini de produs** de pe
internet, în siguranță și politicos, și spune ce arată pagina: **preț**, **monedă**,
**disponibilitate**, **coduri** (cod, cod producător, cod de bare), **marcă**, **poze** și
**descriere**.

Modulul **nu are meniu, ecrane sau date proprii**. Nu decide ce pagini se citesc și nici unde se
scrie rezultatul: asta o fac modulele care îl folosesc (de exemplu `deltatech_vendor_products_site`,
care citește site-ul furnizorului în **Catalog produse furnizor**). Ce aduce modulul, vizibil în
acele module, este:

- un set comun de **stări ale citirii** (**Nouă**, **OK**, **Suspect**, **Alt produs**, **Negăsită**,
  **Blocată**, **Eroare**), cu un **Mesaj citire** în română;
- **sursa** din care s-a citit prețul (**Citit din**: **Date structurate**, **Selectori**, **Tipare
  HTML**);
- două **plase de siguranță** înainte ca un preț să fie folosit: pagina arată **alt produs** decât
  cel așteptat, sau prețul **a sărit** peste un prag;
- un **istoric pe intervale** al valorilor citite (o linie nouă doar când se schimbă o valoare);
- regulile comune de **citire sigură** (doar adrese publice) și **politicoasă** (`robots.txt`, pauză
  între cereri, fără ocolirea protecțiilor anti-robot).

## 2. Bază legală și context

Modulul nu are implicații fiscale sau contabile: nu emite documente, nu generează note contabile și
nu modifică prețuri de vânzare sau de achiziție prin el însuși.

Context operațional important:

- **Întâi feed sau API.** Citirea paginilor este ultima soluție: cereți întâi furnizorului un fișier
  de prețuri sau un acces API.
- **Termenii site-ului.** Citirea automată a unui site (mai ales a unui cont de client B2B) poate fi
  interzisă de termenii site-ului. Verificarea termenilor rămâne în sarcina clientului; modulele care
  folosesc baza cer o confirmare explicită (de exemplu bifa **Citire automată permisă** din
  `deltatech_vendor_products_site`).
- **Politețe.** Baza respectă implicit `robots.txt`: o pagină interzisă de site nu se citește
  (starea **Blocată**). Regula poate fi dezactivată doar de modulul care folosește baza, pe site.
  Între două cereri către același site se păstrează o pauză: 2 secunde în bază, dar valoarea
  efectivă o stabilește modulul care folosește baza (în `deltatech_vendor_products_site`: **Pauză
  între pagini**, implicit 3 secunde).
- **Fără ocolirea protecțiilor.** O pagină de protecție anti-robot (CAPTCHA, verificarea
  Cloudflare „Just a moment...", DataDome, PerimeterX) sau un răspuns HTTP 403, 429 ori 503 dau doar
  starea **Blocată**. Modulul nu încearcă să le ocolească: soluția este un feed sau un API.
- **Siguranța serverului.** Se citesc doar adrese `http`/`https` ale căror servere sunt pe internet
  (adrese IP publice). Adresele din rețeaua locală, `localhost` și adresele interne ale furnizorului
  de cloud sunt refuzate, inclusiv după o redirecționare (cel mult 5). O pagină se citește până la
  3 MiB; un conținut care nu e pagină HTML (de exemplu un PDF) e refuzat.

## 3. Utilizatori și roluri

- **Consultantul / administratorul** trebuie să înțeleagă stările citirii și limitele de mai sus,
  ca să explice clientului de ce o pagină e **Blocată** sau **Suspect** și ce se poate face.
- **Responsabilul achiziții** (sau utilizatorul modulului care folosește baza) citește paginile,
  verifică stările și confirmă prețurile **Suspect**.
- Modulul nu adaugă grupuri sau drepturi de acces: drepturile vin din modulul care îl folosește.
- Rol recomandat la testare: cel cerut de modulul care folosește baza (pentru
  `deltatech_vendor_products_site`: **Achiziții / Administrator**).

## 4. Conturi și date implicate

Nu sunt conturi contabile implicate.

Câmpurile pe care baza le adaugă **pe înregistrările modulelor care o folosesc** (de exemplu pe
rândurile din **Catalog produse furnizor**):

| Câmp | Ce arată |
|------|----------|
| **Adresa paginii** | Pagina de produs citită |
| **Stare citire** | Nouă, OK, Suspect, Alt produs, Negăsită, Blocată, Eroare |
| **Mesaj citire** | Explicația stării, în română (de exemplu „Preț de confirmat: ...") |
| **Ultima citire** | Data și ora ultimei citiri |
| **Citiri eșuate** | Citiri eșuate la rând; de la 5, citirea programată sare peste pagină |
| **Citit din** | Date structurate, Selectori sau Tipare HTML (lista mai are valoarea AI, pe care baza nu o folosește) |

Pe istoricul valorilor citite (de exemplu **Istoric prețuri furnizor**), baza adaugă **De la** și
**Văzut ultima dată**, capetele intervalului în care pagina a arătat aceleași valori.

| Stare | Când apare | Ce faceți |
|-------|------------|-----------|
| **Nouă** | Pagina nu a fost citită încă | Citiți pagina |
| **OK** | Prețul a fost găsit și verificat | Nimic |
| **Suspect** | Prețul diferă de prețul de referință peste prag. Prețul de referință și pragul le stabilește modulul care folosește baza (50% în bază; în `deltatech_vendor_products_site`: referința e **Preț achiziție**, pragul e **Variație suspectă a prețului (%)**, implicit 30%). În modulul furnizorului, Suspect apare și când pagina arată altă monedă decât feed-ul | Comparați cu site-ul și confirmați prețul (la altă monedă, nu confirmați) |
| **Alt produs** | Pagina declară alt cod de bare sau alt cod decât produsul așteptat | Corectați adresa paginii sau codul |
| **Negăsită** | Pagina nu există (HTTP 404/410) sau nu are niciun preț | Verificați adresa paginii |
| **Blocată** | `robots.txt` interzice pagina sau site-ul are protecție anti-robot (în modulul furnizorului și: autentificarea pe site a eșuat) | Cereți un feed sau un API |
| **Eroare** | Adresa lipsește, nu e publică, serverul nu răspunde sau dă alt cod HTTP (de exemplu 500), conținutul nu e HTML | Citiți **Mesaj citire** |

**Date minime pentru demo:** modulul nu are date demo. Demonstrația se face în modulul care îl
folosește (pentru `deltatech_vendor_products_site`: un furnizor, un produs cu linie de furnizor, un
feed **Site furnizor** și câteva pagini de produs).

## 5. Configurare inițială

1. Modulul nu se instalează separat și nu are setări proprii: se instalează automat odată cu un
   modul care îl folosește (de exemplu `deltatech_vendor_products_site`).
2. Pe server trebuie să existe biblioteca Python `extruct` (citirea datelor schema.org); fără ea,
   modulul nu se poate instala. Selectorii de tip **CSS** din modulele care folosesc baza cer și
   biblioteca `cssselect`; fără ea, folosiți **XPath**.
3. Serverul Odoo trebuie să poată ieși pe internet (HTTP/HTTPS) către site-urile citite.
4. Setările citirii (pauza între cereri, respectarea `robots.txt`, pragul de preț suspect,
   selectorii, autentificarea) se fac **în modulul care folosește baza**; pentru
   `deltatech_vendor_products_site`, în fila **Site web** a feed-ului furnizorului.

## 6. Flux de utilizare

Modulul **nu are ecrane proprii**, deci nu are capturi proprii (vezi secțiunea 10). Pașii de mai jos
arată unde se vede efectul lui într-un modul care îl folosește, `deltatech_vendor_products_site`;
capturile indicate sunt ale acelui modul (`deltatech_vendor_products_site/static/description/`, suita
`bitshop_vendor`), iar pașii se urmăresc în fișa lui.

### Pasul 1 — Citirea unei pagini

**Meniu (în modulul care folosește baza):** *Achiziții → Produse → Feed Furnizor → (feed-ul)* →
butonul **Citește paginile acum** (sau acțiunea programată a modulului).

Pentru fiecare pagină, baza face, în această ordine:

1. verifică adresa (doar adrese publice) și `robots.txt`, apoi păstrează pauza față de cererea
   anterioară către același site;
2. citește pagina, urmând redirecționările (cel mult 5); o pagină de protecție anti-robot dă starea
   **Blocată**;
3. caută produsul în **datele schema.org** ale paginii (JSON-LD, Microdata) — pe care majoritatea
   magazinelor le publică pentru motoarele de căutare; dacă site-ul are **selectori** configurați,
   valorile lor completează datele, iar prețul găsit de un selector are prioritate (**Citit din** =
   **Selectori**); ca ultimă soluție, când nu s-a găsit niciun preț, caută prețul în **tiparele HTML**
   obișnuite (prețurile vechi, tăiate, se ignoră);
4. dacă pagina are mai multe oferte, o păstrează pe cea mai ieftină aflată în stoc;
5. citește prețurile scrise în ambele feluri: `1.299,00 lei`, `1,299.00`, `1 299,99`.

**Verificați:** notificarea modulului rezumă câte pagini au ieșit **OK**, **Suspect**, **Alt
produs**, **Negăsită**, **Blocată** sau **Eroare**. Captura modulului care folosește baza:
`05_citeste_paginile.png`.

### Pasul 2 — Citirea stărilor în listă

**Meniu (în modulul care folosește baza):** *Achiziții → Produse → Catalog produse furnizor*,
filtrul **Cu pagină** (sau butonul **Pagini** din formularul feed-ului).

**Găsiți pe ecran:** coloana **Stare citire** (stările din secțiunea 4) și, pe formularul rândului,
**Mesaj citire**, **Ultima citire**, **Citiri eșuate** și **Citit din**.

**Verificați:**
- rândurile **OK** au **Citit din** = **Date structurate** sau **Selectori**; la **Tipare HTML**,
  prețul a fost dedus din pagină și trebuie verificat pe site;
- un rând **Alt produs** nu primește date noi (rămâne cu numele și prețul vechi): codul de bare sau
  codul de pe pagină diferă de cel al rândului. Codul de bare are prioritate: dacă el coincide,
  codurile nu se mai compară. Codurile se compară fără spații, cratime, puncte, `/` și `_`, fără
  diferență între litere mari și mici;
- un rând **Blocată** are în **Mesaj citire** „Site-ul refuză citirea automată (...). Cereți în
  schimb un feed sau un API.";
- după 5 citiri eșuate la rând (**Negăsită**, **Blocată**, **Eroare**), citirea programată nu mai
  citește pagina; orice altă stare (inclusiv **Suspect** sau **Alt produs**) readuce **Citiri
  eșuate** la 0.

Captura modulului care folosește baza: `06_catalog_pagini.png`.

### Pasul 3 — Confirmarea unui preț suspect

**Meniu (în modulul care folosește baza):** *Catalog produse furnizor → (rândul Suspect)* → butonul
**Confirmă prețul**.

Un preț devine **Suspect** când diferă de prețul de referință cu mai mult decât pragul. Pe care preț
îl ia ca referință și ce prag folosește stabilește modulul care folosește baza: în
`deltatech_vendor_products_site`, referința este **Preț achiziție** (ultimul preț acceptat, nu
ultima citire) și pragul **Variație suspectă a prețului (%)**, implicit 30%. **Mesaj citire** arată,
de exemplu, „Preț de confirmat: price 48.0 -> 69.9 (46%)": prețul de referință, prețul nou și
variația; partea de după „:" este un detaliu tehnic, cu punct zecimal. În modulul furnizorului,
Suspect apare și la altă monedă („Pagina arată prețul în EUR, feed-ul este în RON."): acolo **nu
confirmați**, urmați fișa acelui modul.

**Verificați:** comparați prețul cu pagina (**Adresa paginii**). Dacă e corect, **Confirmă prețul**
trece starea în **OK**, iar **Mesaj citire** devine „Preț confirmat de <utilizator>." Unde se scrie
prețul confirmat decide modulul care folosește baza (pentru furnizor: **Preț de confirmat** →
**Preț achiziție**). Captura modulului care folosește baza: `07_pret_suspect.png`.

### Pasul 4 — Istoricul pe intervale

**Meniu (în modulul care folosește baza):** butonul **Istoric** de pe rând (sau *Achiziții → Produse
→ Istoric prețuri furnizor*).

Baza păstrează istoricul ca **intervale**: o linie nouă doar când se schimbă una dintre valorile
urmărite (în `deltatech_vendor_products_site`: prețul de achiziție și disponibilitatea); o citire cu
aceleași valori doar mută **Văzut ultima dată** al ultimei linii. Așa, istoricul nu crește la fiecare
citire.

Ce citiri intră în istoric decide modulul care folosește baza: în `deltatech_vendor_products_site`,
istoricul păstrează și prețul **Suspect**, înainte de confirmare, deși **Preț achiziție** se schimbă
doar la **Confirmă prețul**.

**Verificați:** două citiri cu același preț lasă o singură linie, cu **De la** la prima citire și
**Văzut ultima dată** la a doua; o linie cu un preț Suspect nu înseamnă că prețul a fost acceptat.
Captura modulului care folosește baza: `08_istoric_preturi.png`.

### Note de monografie și raportare

Modulul nu generează note contabile și nu are rapoarte. Valorile citite ajung doar unde le scrie
modulul care folosește baza.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|-------|-----|
| `base` | Singura dependență Odoo |
| `deltatech_vendor_products_site` (suita `bitshop_vendor`) | Folosește baza: citește site-ul furnizorului în **Catalog produse furnizor**, cu stările, confirmarea prețului suspect și **Istoric prețuri furnizor** |

**Ce e automat:**
- verificarea adresei, `robots.txt`, pauza între cereri, recunoașterea paginilor de protecție;
- extragerea datelor schema.org, a selectorilor și a tiparelor de preț;
- marcarea **Alt produs** și **Suspect**, mesajul în română, numărarea citirilor eșuate;
- prelungirea sau deschiderea intervalelor din istoric;
- în citirea programată: paginile citite cel mai demult întâi, site-urile luate pe rând (ca pauza
  unui site să treacă citind celelalte), oprirea când acțiunea programată nu mai are timp.

**Ce rămâne manual:**
- verificarea termenilor site-ului și cererea unui feed sau API;
- confirmarea prețurilor **Suspect** și corectarea adreselor **Alt produs** / **Negăsită**;
- configurarea selectorilor pentru site-urile fără date schema.org.

## 8. Verificări pentru consultant

- [ ] Modulul apare instalat după instalarea unui modul care îl folosește și nu adaugă niciun meniu.
- [ ] O pagină cu date schema.org, pe un site fără selector de preț, iese **OK** (la prima citire sau
      cu prețul în prag), cu **Citit din** = **Date structurate**.
- [ ] O pagină fără preț iese **Negăsită**; o adresă inexistentă (404) tot **Negăsită**.
- [ ] O pagină interzisă de `robots.txt` iese **Blocată** (cu respectarea `robots.txt` activă).
- [ ] O adresă din rețeaua locală (de exemplu `http://localhost/...` sau `http://192.168.1.10/...`)
      iese **Eroare** și nu se citește.
- [ ] O pagină cu alt cod de bare decât produsul iese **Alt produs** și nu aduce date noi.
- [ ] Un preț cu salt peste prag iese **Suspect**; **Confirmă prețul** îl trece în **OK** cu „Preț
      confirmat de ...".
- [ ] La **Tipare HTML**, prețul a fost verificat manual pe site.
- [ ] Două citiri cu același preț lasă o singură linie în istoric, cu **Văzut ultima dată** mutat.
- [ ] O pagină cu 5 citiri eșuate la rând nu mai e citită de acțiunea programată.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|-------|-------|-----------|
| „Site-ul refuză citirea automată (forbidden by robots.txt). ..." | `robots.txt` interzice pagina | Cereți un feed sau un API; dezactivarea `robots.txt` se face doar în modulul care folosește baza, după verificarea termenilor |
| „Site-ul refuză citirea automată (HTTP 403: protection against robots). ..." | Pagină de protecție anti-robot sau răspuns 403/429/503 | Nu se ocolește; cereți un feed sau un API |
| „Pagina arată alt produs: ..." | Codul de bare sau codul de pe pagină diferă de cel așteptat | Corectați **Adresa paginii** sau codul produsului |
| „Niciun preț pe pagină (no price on the page)." | Pagina nu are date schema.org, selectorii nu găsesc prețul, tiparele HTML nu îl găsesc | Configurați selectori pentru site |
| „Niciun preț pe pagină (HTTP 404)." | Pagina nu mai există | Corectați sau ștergeți adresa paginii |
| „Preț de confirmat: price 48.0 -> 69.9 (46%)" | Salt de preț peste prag, față de prețul de referință | Verificați pe site și apăsați **Confirmă prețul** |
| „Pagina arată prețul în EUR, feed-ul este în RON." (modulul furnizorului) | Moneda paginii diferă de moneda feed-ului; rândul e **Suspect** | Nu confirmați; vedeți fișa `deltatech_vendor_products_site` |
| „Pagina nu a putut fi citită: HTTP 500" | Site-ul a răspuns cu o eroare (orice cod în afară de 200, 404/410 și 403/429/503) | Reîncercați mai târziu; verificați pagina în browser |
| „Pagina nu a putut fi citită: the host ... points to a non-public address (...)" | Adresa duce într-o rețea privată sau la `localhost` | Folosiți adresa publică a site-ului |
| „Pagina nu a putut fi citită: cannot resolve the host ..." | Numele site-ului nu există sau serverul nu are DNS | Verificați adresa și ieșirea serverului pe internet |
| „Pagina nu a putut fi citită: unexpected content type ..." | Adresa duce la un fișier (PDF, imagine), nu la o pagină HTML | Folosiți adresa paginii de produs |
| „Pagina nu a putut fi citită: too many redirects" | Mai mult de 5 redirecționări | Folosiți adresa finală a paginii |
| „Pagina nu a putut fi citită: fără adresa paginii" | Rândul nu are **Adresa paginii** | Completați adresa |

Detaliul tehnic din mesaj (dintre paranteze sau de după „:") rămâne în engleză. Blocarea la
autentificarea pe site ține de `deltatech_vendor_products_site`: vedeți fișa lui.

## 10. Capturi de ecran

Modulul **nu are capturi proprii**, intenționat: nu are meniu, formulare, liste, asistenți sau
rapoarte; câmpurile și stările lui apar doar pe ecranele modulelor care îl folosesc. O captură
proprie ar arăta, de fapt, un ecran al altui modul. Din același motiv, modulul nu are
`tests/test_screenshots.py`.

Capturile care arată efectul bazei sunt ale modulului `deltatech_vendor_products_site` (suita
`bitshop_vendor`, folderul `static/description/`), generate automat de testul lui de capturi, în RO:

1. `05_citeste_paginile.png` — rezumatul stărilor după citirea paginilor (pasul 1).
2. `06_catalog_pagini.png` — **Catalog produse furnizor** cu coloana **Stare citire** (pasul 2).
3. `07_pret_suspect.png` — rândul **Suspect**, cu **Mesaj citire** și **Confirmă prețul** (pasul 3).
4. `08_istoric_preturi.png` — **Istoric prețuri furnizor**, pe intervale (pasul 4).

Imaginile din `static/description/` ale acestui modul (`icon.*`, `main_screenshot.*`) sunt doar
iconița și bannerul pentru Odoo Apps, nu capturi ale fluxului.

## 11. Observații pentru manual

- Prezentați modulul ca „motorul de citire a paginilor" comun, nu ca aplicație: utilizatorul nu îl
  vede niciodată direct, ci doar stările din modulele care îl folosesc.
- Păstrați tabelul stărilor din secțiunea 4: stările sunt aceleași în toate modulele care folosesc
  baza; pragul de preț suspect, prețul de referință și pauza între cereri le stabilește fiecare
  modul (pentru furnizor: 30% față de **Preț achiziție**, 3 secunde).
- Subliniați cele două plase de siguranță — **Alt produs** și **Suspect** — și faptul că un preț
  citit din **Tipare HTML** trebuie verificat pe site.
- Spuneți clar că protecțiile anti-robot și `robots.txt` nu se ocolesc: soluția corectă este un feed
  sau un API de la furnizor.
