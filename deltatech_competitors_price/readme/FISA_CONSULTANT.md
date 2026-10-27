# Fișă Modul: Urmărirea prețurilor concurenței pe produs

**Modul:** `deltatech_competitors_price`
**Utilizator principal:** Responsabil vânzări / pricing, Operator achiziții
**Prioritate:** 🟢 Scăzută (informație comercială; nu modifică prețurile proprii)

---

## 1. Scop business

Echipele de vânzări și achiziții compară des prețurile proprii cu cele ale concurenței, deschizând
site-urile concurenților și notând prețurile în fișiere separate. Modulul
`deltatech_competitors_price` adaugă pe fișa produsului tabul **Prețuri concurenți**, în care se
înregistrează, pentru fiecare concurent, adresa paginii produsului de pe site-ul lui. La cerere,
Odoo citește pagina și aduce **ultimul preț** afișat, cu moneda, data preluării și starea preluării.
Comparația se face direct în Odoo, lângă prețul de vânzare propriu.

## 2. Bază legală și context

Nu există temei legal — este un instrument de analiză comercială. Modulul citește doar pagini publice
de produs (adrese web publice, `http`/`https`); adresele interne sau private sunt refuzate.

## 3. Utilizatori și roluri

Responsabil vânzări / pricing, Operator achiziții, orice utilizator intern.

Roluri recomandate pentru testare:
- Utilizator intern: adaugă concurenți și adrese pe produs, preia prețurile
- Administrator funcțional: verifică bibliotecile necesare pe server și comportamentul la erori

Toți utilizatorii interni pot crea, modifica și șterge liniile de preț ale concurenților.

## 4. Conturi și date implicate

Modulul nu generează note contabile și nu folosește conturi.

Date minime pentru demo:
- un produs (șablon de produs) cu preț de vânzare
- adresa publică a paginii aceluiași produs pe site-ul a 1–2 concurenți
- acces la internet de pe serverul Odoo

## 5. Configurare inițială

1. Instalați modulul `deltatech_competitors_price` (depinde de `product`). Pe server trebuie să
   existe bibliotecile Python `requests` și `lxml`; `extruct` și `w3lib` (declarate ca dependențe
   externe) permit citirea datelor structurate ale paginii și cresc precizia.
2. Verificați că serverul Odoo are acces la internet către site-urile concurenților.
3. Nu sunt necesare meniuri sau setări noi.

## 6. Flux de utilizare

### Pasul 1 — Adăugarea concurenților pe produs

Accesați **Vânzări → Produse → Produse** (sau **Achiziții → Produse → Produse**), deschideți
produsul și mergeți în tabul **Prețuri concurenți**. Adăugați câte o linie pentru fiecare concurent:
- **Concurent** — numele concurentului (ex. „Altex”);
- **URL produs** — adresa completă a paginii produsului pe site-ul concurentului.

Salvați produsul.

### Pasul 2 — Preluarea prețului

Pe linia concurentului apăsați **Preia**. Odoo descarcă pagina și caută prețul, mai întâi în datele
structurate ale paginii (informațiile de produs pe care site-urile le publică pentru motoarele de
căutare), apoi în elementele de preț din pagină. Pe linie se completează:
- **Ultimul preț** — prețul găsit;
- **Moneda** — moneda găsită pe pagină, dacă există în Odoo (coloană opțională, ascunsă implicit);
- **Ultima preluare** — data și ora preluării;
- **Preluare stare** — „OK” la succes sau motivul eșecului (ex. „Prețul nu a fost găsit pe pagină”).

### Pasul 3 — Compararea cu prețul propriu

1. **Găsiți** în tabul **Prețuri concurenți** coloanele **Ultimul preț** și **Ultima preluare**
   pentru fiecare concurent.
2. **Verificați** că **Preluare stare** este „OK” și că data preluării este recentă; deschideți
   adresa concurentului și confirmați că prețul preluat este prețul real de vânzare (nu un preț vechi,
   un preț redus de pe altă variantă sau rata lunară).
3. **Treceți mai departe** — comparați cu **Prețul de vânzare** al produsului din tabul
   **Informații generale** și decideți ajustarea prețului propriu (modulul nu schimbă prețul automat).

### Pasul 4 — Marcarea liniilor pentru preluare programată

Bifați **Preluare automată** (coloană opțională, ascunsă implicit) pe liniile care ar trebui
actualizate periodic. Atenție: modulul **nu** include o acțiune programată; bifa doar marchează
liniile pentru o automatizare care poate fi adăugată ulterior. Până atunci, preluarea se face manual,
cu **Preia**, linie cu linie.

### Note de monografie și raportare

Modulul nu generează note contabile și nu modifică prețurile de vânzare sau listele de prețuri.
Prețurile concurenței sunt doar informative.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `product` | fișa produsului (șablon), unde se afișează tabul **Prețuri concurenți** | dependență (manifest) |

Ce este automat: descărcarea paginii, extragerea prețului și a monedei, completarea datei și a
stării preluării, refuzarea adreselor interne/nepublice.
Ce rămâne manual: introducerea concurenților și a adreselor, lansarea preluării (**Preia**),
verificarea prețului găsit și decizia de preț.

## 8. Verificări pentru consultant

- [ ] Tabul **Prețuri concurenți** apare pe formularul produsului.
- [ ] O linie nouă se poate adăuga cu **Concurent** și **URL produs**.
- [ ] **Preia** completează **Ultimul preț**, **Ultima preluare** și **Preluare stare** = „OK” pe o
      pagină publică de produs.
- [ ] Pe o pagină fără preț, **Preluare stare** = „Prețul nu a fost găsit pe pagină”, iar ultimul
      preț anterior rămâne neschimbat.
- [ ] O adresă internă (ex. `http://localhost` sau o adresă IP privată) este refuzată, cu motivul
      în **Preluare stare**.
- [ ] O adresă care nu începe cu `http`/`https` este refuzată.
- [ ] Moneda liniei se actualizează când pagina publică moneda (ex. RON, EUR).
- [ ] Prețul de vânzare al produsului nu este modificat de preluare.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| „Nu există URL de produs pe linia concurentului.” | **URL produs** este gol | Completați adresa paginii produsului |
| „Prețul nu a fost găsit pe pagină” (în **Preluare stare**) | Pagina nu publică prețul în mod citibil (încărcat dinamic, ascuns) | Verificați manual pagina; pentru site-uri importante se pot adăuga reguli dedicate |
| „The product URL must be an http(s) address: …” | Adresa nu începe cu `http://` sau `https://` | Copiați adresa completă din browser |
| „The product URL points to a non-public address …” / „Cannot resolve the host …” | Adresă internă, privată sau domeniu inexistent | Folosiți adresa publică a site-ului concurentului |
| Mesaj de eroare HTTP (ex. 403, 404) în **Preluare stare** | Pagina nu mai există sau site-ul blochează cererile automate | Actualizați adresa sau verificați manual prețul |
| „Missing requests/lxml libraries; cannot fetch.” | Bibliotecile Python lipsesc pe server | Instalarea bibliotecilor de către administratorul serverului |
| Preț greșit (ex. rata lunară sau prețul altui produs) | Pagina nu are date structurate, iar prețul a fost ghicit din elementele paginii | Verificați manual; folosiți adresa exactă a variantei produsului |

## 10. Capturi de ecran

Fișa este **doar text** — nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele prin
etichetele lor reale din interfață. Dacă se decide ulterior completarea cu capturi, se rulează
skill-ul `fisa-screenshots`, care generează imaginile din `tests/test_screenshots.py` (mixinul
`ScreenshotCase`), în română, iar secțiunile 6 și 10 se actualizează în consecință.

## 11. Observații pentru manual

Prezentați modulul ca instrument de documentare a prețurilor concurenței, nu ca motor de pricing:
prețul se preia la cerere și se verifică întotdeauna pe pagina concurentului. Precizați că
**Preluare automată** este doar o marcare (fără acțiune programată livrată) și că preluarea se face
linie cu linie, cu **Preia**; descrierea modulului pomenește un buton la nivel de produs pentru toate
liniile, dar acesta nu apare în interfața versiunii 20.0. Câteva mesaje de eroare (adresă nepublică,
adresă fără `http`) apar momentan în engleză.
