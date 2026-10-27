# Fișă Modul: Liste de materiale de bază pentru variante

**Modul:** `deltatech_mrp_bom`
**Utilizator principal:** Tehnolog / responsabil producție
**Prioritate:** 🟡 Medie (esențial la producția cu multe variante; fără efect contabil propriu)

---

## 1. Scop business

Un produs cu variante (culoare, dimensiune, material) are de obicei aceeași rețetă pentru toate
variantele, dar cu **componente care diferă după variantă**: un dulap alb folosește plăci albe, unul
negru plăci negre. În Odoo standard, fie se întreține câte o listă de materiale pentru fiecare variantă,
fie se pun pe aceeași listă toate componentele, fiecare restricționată la anumite variante.

Modulul introduce o **listă de bază** (*Base*) pe șablonul produsului, din care se generează automat câte
o **listă derivată** (*Derived*) pentru fiecare variantă fabricată. În lista derivată, fiecare componentă
cu variante este înlocuită cu varianta potrivită atributelor produsului fabricat (aceeași culoare, aceeași
dimensiune). Tehnologul întreține o singură rețetă, iar comenzile de producție consumă componentele
corecte.

## 2. Bază legală și context

Modulul nu are implicații fiscale și nu generează note contabile proprii. Contextul este tehnologic:
întreținerea rețetelor de fabricație și consumul corect de materiale pe comenzile de producție, cu efect
indirect asupra costului produselor finite (prin consumurile standard ale comenzilor).

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Tehnolog | Creează lista de bază, marchează tipul listelor, recalculează listele derivate |
| Planificator / responsabil producție | Creează și confirmă comenzile de producție; lista derivată se generează automat |
| Consultant | Configurează atributele comune între produsul finit și componente |

Roluri recomandate pentru testare: **Manufacturing / Administrator** (liste de materiale) și
**Manufacturing / User** (comenzi de producție).

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile direct. Consumurile comenzilor de producție urmează contabilizarea
standard (vezi „Note de monografie”).

Date minime pentru demo:

- un atribut comun, de exemplu *Culoare* cu valorile *Alb* și *Negru*, activat pe variante;
- un produs finit cu variante după *Culoare* (de exemplu *Dulap*);
- o componentă cu aceleași variante (de exemplu *Placă* Albă / Neagră) și o componentă fără variante (de
  exemplu *Șuruburi*).

## 5. Configurare inițială

1. Instalați modulul `deltatech_mrp_bom` (depinde de `mrp`).
2. Activați variantele de produs (**Inventory → Configuration → Settings**, **Variants**).
3. Creați lista de bază: **Manufacturing → Products → Bills of Materials → New**, produsul = șablonul
   *Dulap* (fără variantă), **Base Type** = *Base*. Adăugați componentele, alegând orice variantă a
   componentei cu variante (de exemplu *Placă (Alb)*); varianta corectă se alege la derivare. Dacă vreo
   componentă sau operație privește doar anumite variante, restricționați-o standard, pe variante.
4. Opțional, setați cantitatea produsă de listă (de exemplu 10 bucăți) și operațiile; ele se copiază în
   listele derivate.

## 6. Flux de utilizare

### Pasul 1 — Tipul listei de materiale

Pe formularul listei de materiale, câmpul **Base Type**, înaintea tipului standard al listei, are trei
valori:

- *Normal* — comportamentul standard Odoo (implicit);
- *Base* — rețeta-șablon a produsului, folosită ca sursă pentru variante;
- *Derived* — lista unei variante, generată din lista de bază.

### Pasul 2 — Generarea listei derivate din comanda de producție

**Manufacturing → Operations → Manufacturing Orders → New**. Alegeți varianta de fabricat (de exemplu
*Dulap (Negru)*).

Ce se întâmplă: dacă șablonul produsului are o listă *Base*, modulul caută lista *Derived* a variantei;
dacă nu există, o creează, cu referința **D1**, **D2**... (numărul de ordine al variantei derivate pe acel
produs). Lista derivată copiază din lista de bază cantitatea produsă și unitatea, componentele (cu
varianta potrivită atributelor variantei fabricate), operațiile cu dependențele lor și subprodusele,
omițând ce este restricționat la alte variante. Comanda primește lista derivată și componentele ei.

Pe o comandă în ciornă care are încă lista de bază, butonul **Compute Derived BoM** din antet face același
lucru la cerere.

### Pasul 3 — Verificarea componentelor pe comandă

Pe comanda de producție, pagina componentelor: găsiți fiecare componentă cu variante și verificați că
varianta ei are aceleași valori de atribut ca produsul fabricat (pentru *Dulap (Negru)*, *Placă
(Negru)*); componentele fără variante apar neschimbate. Verificați și cantitățile: la o listă de bază
pentru 10 bucăți cu 20 de plăci, o comandă de 10 bucăți consumă 20 de plăci.

### Pasul 4 — Confirmarea comenzii

Apăsați **Confirm**. Înainte de confirmare, dacă lista comenzii nu este de tip *Normal*, lista derivată
se recalculează din lista de bază, ca să prindă ultimele modificări ale rețetei.

### Pasul 5 — Recalcularea unei liste derivate

După o modificare a listei de bază, deschideți o listă derivată (**Manufacturing → Products → Bills of
Materials**, filtrați după produs) și apăsați **Recompute Components** în antet (butonul apare doar pe
listele *Derived*). Componentele și subprodusele sunt înlocuite cu cele din lista de bază; operațiile
vechi sunt arhivate (nu șterse), ca ordinele de lucru existente să-și păstreze operația.

### Pasul 6 — Navigarea în sub-liste

În lista de componente a oricărei liste de materiale, componentele care au propria listă de materiale au
butonul **Show**, care deschide direct sub-lista componentei.

Raportul de structură a listei (**BoM Overview**), deschis pentru o variantă a unui produs cu listă de
bază, generează sau recalculează lista derivată a variantei și o afișează pe aceasta.

### Note de monografie și raportare

Modulul nu generează note contabile proprii. Comanda de producție care folosește lista derivată se
contabilizează standard, în evaluarea perpetuă, de exemplu:

- consumul componentelor: Dr 601 „Cheltuieli cu materiile prime” / Cr 301 „Materii prime”;
- obținerea produsului finit: Dr 345 „Produse finite” / Cr 711 „Venituri aferente costurilor stocurilor
  de produse”.

Conturile exacte depind de categoriile produselor și de configurarea evaluării stocului.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `mrp` | listele de materiale, comenzile de producție, raportul de structură |
| `product` | variantele și atributele după care se aleg componentele |

**Ce e automat:** crearea listei derivate la alegerea variantei pe comandă, referința **Dn**, alegerea
variantei componentelor după atribute, copierea cantității, operațiilor și subproduselor, recalcularea la
confirmare.

**Ce rămâne manual:** întreținerea listei de bază, recalcularea listelor derivate existente după
modificarea rețetei (**Recompute Components**), definirea atributelor comune pe componente.

## 8. Verificări pentru consultant

- [ ] Pe o comandă pentru o variantă nouă se creează o listă *Derived* cu referința **D1** (apoi **D2**
  pentru următoarea variantă).
- [ ] Componentele cu variante din lista derivată au aceleași valori de atribut ca varianta fabricată.
- [ ] Lista derivată are aceeași cantitate produsă și unitate ca lista de bază; consumul pe comandă
  respectă proporția.
- [ ] Componentele, operațiile și subprodusele restricționate la alte variante nu apar în lista
  derivată.
- [ ] **Compute Derived BoM** apare doar pe comenzile în ciornă cu listă *Base*.
- [ ] După modificarea listei de bază, **Recompute Components** actualizează lista derivată, iar
  operațiile vechi sunt arhivate.
- [ ] Butonul **Show** deschide sub-lista unei componente semifabricate.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Componenta apare cu varianta greșită sau neschimbată | Componenta folosește alt atribut decât produsul finit (de exemplu un al doilea atribut *Culoare*, creat separat) sau nu are valoarea respectivă | Folosiți pe produsul finit și pe componentă același atribut (aceeași înregistrare din **Attributes**), cu aceleași valori |
| Lista derivată nu se creează | Șablonul produsului nu are o listă cu **Base Type** = *Base* | Marcați lista de bază |
| Comanda consumă după rețeta veche | Lista derivată nu a fost recalculată după modificarea listei de bază | **Recompute Components** pe lista derivată sau reconfirmați comanda din ciornă |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița, bannerul, sigla și imaginea principală pentru Odoo Apps) și nici test
`tests/test_screenshots.py`. Dacă se doresc capturi, ele se generează cu skill-ul `fisa-screenshots`
(lista de bază, comanda cu lista derivată, butonul **Compute Derived BoM**, lista derivată cu **Recompute
Components**) și se leagă apoi în pașii din secțiunea 6.

## 11. Observații pentru manual

- Regula de potrivire a componentelor (aceeași înregistrare de atribut pe produsul finit și pe
  componentă) este cheia
  modulului și trebuie explicată cu un exemplu.
- Listele derivate nu se editează de mână: orice modificare se pierde la următoarea recalculare; rețeta
  se întreține în lista de bază.
