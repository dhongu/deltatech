# Fișă Modul: Livrare directă — adresa de livrare pe transfer și controlul prețului de achiziție

**Modul:** `deltatech_dropshipping`
**Utilizator principal:** Operator vânzări, Operator achiziții, Gestionar
**Prioritate:** 🟡 Medie (previne vânzarea în pierdere și livrarea la adresa greșită în livrarea directă)

---

## 1. Scop business

În livrarea directă (dropshipping), marfa pleacă de la furnizor direct la client, pe baza unei comenzi
de achiziție generate din comanda de vânzare. Două probleme apar des:

- pe transfer nu se vede clar **unde ajunge marfa** (adresa de livrare a clientului), mai ales când
  clientul are o adresă de livrare diferită de cea de facturare;
- prețul de achiziție de la furnizor poate depăși prețul de vânzare către client, iar vânzarea se face
  în pierdere fără ca cineva să observe.

Modulul `deltatech_dropshipping` adaugă pe transferuri câmpul **Livrare la** (adresa de livrare) și
afișează pe comanda de achiziție un **avertisment** când prețul de achiziție al unei linii este mai
mare decât prețul de vânzare al liniei de comandă de vânzare din care provine, ambele fără TVA.

## 2. Bază legală și context

Nu există temei legal specific — este un control operațional și comercial. Adresa de livrare corectă
pe transfer ajută la întocmirea documentelor de însoțire a mărfii; controlul de preț este un
instrument de marjă, nu o regulă fiscală.

## 3. Utilizatori și roluri

Operator vânzări, Operator achiziții, Gestionar.

Roluri recomandate pentru testare:
- Utilizator vânzări: creează comanda de vânzare pentru un produs cu ruta de livrare directă
- Utilizator achiziții: verifică comanda de achiziție generată și avertismentul de preț
- Gestionar: verifică adresa **Livrare la** pe transferuri și în lista de transferuri

## 4. Conturi și date implicate

Modulul nu generează note contabile și nu folosește conturi.

Date minime pentru demo:
- un client cu o **adresă de livrare** separată (contact de tip „Adresă de livrare”)
- un furnizor cu preț de furnizor pe produs
- un produs cu ruta **Livrare directă** activă și cu preț de vânzare
- (pentru avertisment) un preț de furnizor mai mare decât prețul de vânzare

## 5. Configurare inițială

1. Instalați modulul `deltatech_dropshipping` (depinde de `stock_dropshipping` și `sale_purchase`).
2. Activați ruta de livrare directă și setați-o pe produs (tab **Inventar → Rute → Livrare directă**),
   conform configurării standard Odoo.
3. Adăugați pe produs furnizorul și prețul de achiziție (tab **Achiziție**).
4. Nu sunt necesare setări sau meniuri noi.

## 6. Flux de utilizare

### Pasul 1 — Comanda de vânzare cu adresă de livrare

Accesați **Vânzări → Comenzi → Comenzi**, creați o comandă pentru client, alegeți la **Adresă
livrare** adresa de livrare a clientului și adăugați produsul cu ruta de livrare directă. Apăsați
**Confirmă**. Odoo generează automat comanda de achiziție către furnizor (cerere de ofertă).

### Pasul 2 — Avertismentul de preț pe comanda de achiziție

Deschideți comanda de achiziție generată (**Achiziții → Comenzi → Cereri de ofertă** sau din butonul
inteligent de pe comanda de vânzare). Dacă prețul unitar de achiziție al unei linii, fără TVA, este
mai mare decât prețul unitar de vânzare al liniei de vânzare corespunzătoare, fără TVA, sub bara de
butoane apare un chenar galben: „The following products have a purchase price higher than the sale
price:”, urmat de câte un rând pe produs, de forma
**Produs**: Purchase *preț achiziție* > Sale *preț vânzare* (Diff: *diferență*).

1. **Găsiți** chenarul galben imediat sub antetul comenzii și rândul fiecărui produs afectat.
2. **Verificați** pentru fiecare rând dacă diferența este reală (preț de furnizor actualizat, preț de
   vânzare greșit) sau o consecință a unei unități de măsură / monede / reduceri diferite între cele
   două documente (vezi secțiunea 9).
3. **Treceți mai departe** — corectați prețul de achiziție (negociere cu furnizorul) sau prețul de
   vânzare (cu acordul vânzărilor), apoi confirmați comanda. Avertismentul dispare automat când
   prețurile nu mai sunt în pierdere. Avertismentul nu blochează confirmarea.

### Pasul 3 — Adresa de livrare pe transfer

Confirmați comanda de achiziție. Deschideți transferul de livrare directă (din butonul inteligent al
comenzii sau din **Inventar → Operații → Transferuri**). Lângă **Contact** apare câmpul
**Livrare la**:
- pe transferurile de livrare directă și de recepție legate de o comandă de vânzare — **adresa de
  livrare** a comenzii de vânzare (adresa clientului unde ajunge marfa);
- pe transferurile de ieșire (livrări) — chiar contactul transferului;
- pe celelalte transferuri, fără comandă de vânzare — adresa depozitului.

### Pasul 4 — Adresa de livrare în lista de transferuri

În **Inventar → Operații → Transferuri**, coloana **Livrare la** apare lângă **Contact** (coloană
opțională, afișată implicit). Folosiți-o pentru a verifica dintr-o privire destinația fiecărei
livrări directe.

### Note de monografie și raportare

Modulul nu generează note contabile. Livrarea directă se contabilizează după fluxul standard Odoo
(factura furnizorului și factura clientului); modulul doar afișează informații suplimentare.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `stock_dropshipping` | ruta și transferul de livrare directă | dependență (manifest) |
| `sale_purchase` | legătura dintre linia de achiziție și linia de vânzare | dependență (manifest) |

Ce este automat: calculul adresei **Livrare la** pe transferuri, compararea prețurilor fără TVA și
afișarea avertismentului.
Ce rămâne manual: decizia comercială la un avertisment de preț (corectarea prețurilor sau acceptarea
pierderii).

## 8. Verificări pentru consultant

- [ ] Câmpul **Livrare la** apare pe formularul transferului, lângă **Contact**.
- [ ] Pe transferul de livrare directă, **Livrare la** este adresa de livrare a comenzii de vânzare.
- [ ] Coloana **Livrare la** apare în lista de transferuri.
- [ ] Cu preț de achiziție mai mare decât prețul de vânzare (fără TVA), comanda de achiziție afișează
      chenarul galben cu produsul, prețurile și diferența.
- [ ] Cu preț de achiziție mai mic sau egal, chenarul nu apare.
- [ ] Modificarea prețului de achiziție actualizează imediat avertismentul.
- [ ] Prețurile comparate sunt fără TVA (o taxă inclusă în preț nu produce un avertisment fals).
- [ ] Avertismentul nu împiedică confirmarea comenzii.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| Avertisment de preț deși vânzarea nu este în pierdere | Comparația ignoră unitatea de măsură, moneda și reducerea (discountul) liniilor — problemă cunoscută, [dhongu/deltatech#3384](https://github.com/dhongu/deltatech/issues/3384) | Verificați manual marja când documentele au UM, monedă sau discount diferite |
| Avertismentul nu apare deloc | Linia de achiziție nu provine dintr-o comandă de vânzare (achiziție creată manual) | Normal: controlul se face doar pe liniile legate de o linie de vânzare |
| **Livrare la** arată adresa depozitului | Transferul nu este legat de o comandă de vânzare | Verificați originea transferului |
| **Livrare la** arată adresa de facturare a clientului | Comanda de vânzare nu are **Adresă livrare** separată | Completați adresa de livrare pe comanda de vânzare înainte de confirmare |

## 10. Capturi de ecran

Fișa este **doar text** — nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele prin
etichetele lor reale din interfață. Dacă se decide ulterior completarea cu capturi, se rulează
skill-ul `fisa-screenshots`, care generează imaginile din `tests/test_screenshots.py` (mixinul
`ScreenshotCase`), în română, iar secțiunile 6 și 10 se actualizează în consecință.

## 11. Observații pentru manual

Prezentați modulul în capitolul de livrare directă, ca două ajutoare: „unde pleacă marfa” (câmpul
**Livrare la**) și „nu vindem în pierdere” (avertismentul de pe comanda de achiziție). Textul
avertismentului apare momentan în engleză. Precizați că prețurile se compară fără TVA și că, până la
rezolvarea problemei cunoscute, comparația nu ține cont de unitatea de măsură, monedă și discount.
