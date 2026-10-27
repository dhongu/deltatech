# Fișă Modul: Liste de produse definite prin filtru

**Modul:** `deltatech_product_list`
**Utilizator principal:** Responsabil de vânzări / e-commerce (definește ce produse intră într-o
listă), implementator (leagă listele de feed-uri și integrări)
**Prioritate:** 🟢 Scăzută (modul de bază pentru alte module; singur nu schimbă niciun flux)

---

## 1. Scop business

Mai multe procese au nevoie de „o listă de produse” stabilită după o regulă: produsele trimise
către un marketplace, cele dintr-un catalog pentru un partener, produsele unei campanii. Dacă lista
se ține de mână, ea rămâne în urmă ori de câte ori apare un produs nou. Modulul introduce
documentul **Listă produse**: un nume, un **filtru** pe produse (de exemplu produsele bifate la
**Vânzări**, din categoria „Electrocasnice”) și o **limită** a numărului de produse. Lista nu memorează produse, ci
regula: la fiecare folosire, ea conține produsele care îndeplinesc filtrul în acel moment.

Modulul este o **fundație**: listele sunt folosite de alte module, în primul rând de
`deltatech_feed` (suita bitshop), care generează din ele feed-urile de produse pentru Google,
eMAG, Compari și alte platforme.

## 2. Bază legală și context

- Modulul **nu are efect fiscal sau contabil**: nu creează documente și nu modifică produsele.
- Lista este doar o selecție de produse. Prețurile, stocul și datele exportate le stabilește
  modulul care folosește lista (de exemplu, feed-ul).

## 3. Utilizatori și roluri

| Rol | Ce poate face |
|---|---|
| **Vânzări: Utilizator: Numai documente proprii** sau mai mult | creează, modifică, arhivează și șterge liste de produse |
| Orice utilizator intern | vede listele de produse (le pot folosi alte module) |

Listele sunt pe companie (lista primește compania curentă la creare): fiecare utilizator vede doar
listele companiilor la care are acces.

Roluri recomandate pentru testare:
- un **agent de vânzări**, care creează și modifică o listă;
- un utilizator intern fără drepturi de vânzări, care trebuie doar să o vadă.

## 4. Conturi și date implicate

Modulul **nu generează note contabile** și nu atinge conturi. Date minime pentru demo:

- categoria **Toate / Electrocasnice**, cu 5 produse vandabile (de exemplu „Fierbător electric
  1,7 l”, „Prăjitor de pâine”, „Mixer vertical”, „Cafetieră”, „Storcător”) și un produs nevandabil
  („Piesă de schimb mixer”, cu **Vânzări** debifat);
- lista **Electrocasnice — feed eMAG**, cu filtrul **Vânzări** este setat și **Categorie produs** este „Electrocasnice”,
  limita 80.

## 5. Configurare inițială

1. Instalați `deltatech_product_list` (dependențe: `product`, `sale`). Meniul **Listă produse**
   apare în **Vânzări → Produse**.
2. Nu e nevoie de altă setare. Pentru feed-uri, instalați și `deltatech_feed`, care adaugă pe listă
   tipul feed-ului, lista de prețuri și linkul de publicare.

## 6. Flux de utilizare

### Pasul 1 — Lista listelor de produse

Deschideți **Vânzări → Produse → Listă produse**. Ecranul arată listele existente, după **Nume**.
Apăsați **Nou** pentru o listă nouă.

### Pasul 2 — Crearea unei liste

În formular completați:

- **Nume** — de exemplu „Electrocasnice — feed eMAG”;
- **Produse**, în grupul **Filtru** — regula de selecție. O listă nouă pornește cu regula **Vânzări** este
  setat (produsele bifate ca vandabile). Apăsați pe filtru pentru a-l edita în fereastra de filtre a Odoo: adăugați o
  condiție nouă, de exemplu **Categorie produs** este „Electrocasnice”. Sub filtru, Odoo arată câte
  produse îndeplinesc regula în acel moment;
- **Limită** — numărul maxim de produse folosite din listă (implicit 80).

Salvați.

**Verificați:** numărul de înregistrări afișat sub filtru este 5 (cele cinci produse vandabile din
categorie); piesa de schimb, care nu se vinde, nu este numărată. Filtrul se aplică pe **variantele**
de produs: un produs cu trei variante contează de trei ori.

### Pasul 3 — Limita și arhivarea

**Limită** se aplică de modulul care folosește lista: dacă filtrul găsește mai multe produse decât
limita, se folosesc doar primele, până la limită. Pentru o listă „toate produsele”, măriți limita
peste numărul de produse din nomenclator.

O listă care nu mai e folosită se arhivează din rotița ⚙ → **Arhivează**; formularul ei primește
banda roșie **Arhivat** și nu mai apare în **Listă produse**. Înainte de arhivare, verificați că
lista nu mai este folosită de un feed sau de o integrare.

### Note de monografie și raportare

Modulul **nu înregistrează nicio notă contabilă** și nu adaugă rapoarte. Produsele din listă nu se
memorează: o listă reflectă mereu nomenclatorul la zi, deci un produs nou care îndeplinește filtrul
intră singur în listă.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux |
|---|---|
| `product` | produsele (variantele) pe care se aplică filtrul |
| `sale` | meniul **Vânzări → Produse** și dreptul de a modifica listele |
| `deltatech_feed` (suita bitshop) | folosește listele pentru feed-urile de produse (Google, eMAG, Compari, CSV etc.) |

Ce este automat: actualizarea conținutului listei când se schimbă produsele, aplicarea limitei de
modulul care folosește lista.

Ce rămâne manual: definirea filtrului și a limitei, arhivarea listelor nefolosite.

## 8. Verificări pentru consultant

- [ ] Meniul **Vânzări → Produse → Listă produse** există pentru un agent de vânzări.
- [ ] O listă nouă pornește cu filtrul **Vânzări** este setat și limita 80.
- [ ] Filtrul **Vânzări** + categoria „Electrocasnice” numără 5 înregistrări în demo.
- [ ] Un produs nou, vandabil, din categoria „Electrocasnice” crește numărul la 6 fără nicio
      modificare a listei.
- [ ] O listă arhivată are banda **Arhivat** și dispare din lista implicită.
- [ ] Un utilizator dintr-o altă companie nu vede lista creată pe compania demo.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Meniul **Listă produse** lipsește | Utilizatorul nu are niciun drept în **Vânzări** | Acordați cel puțin **Vânzări: Utilizator: Numai documente proprii** |
| Lista nu se poate salva sau modifica (eroare de acces) | Utilizatorul vede listele, dar nu are drepturi de vânzări | Acordați cel puțin **Vânzări: Utilizator: Numai documente proprii** sau lăsați modificarea unui agent de vânzări |
| Feed-ul are mai puține produse decât arată filtrul | **Limită** este mai mică decât numărul de produse găsite | Măriți **Limită** |
| Un produs apare de mai multe ori în feed | Produsul are variante, iar lista lucrează pe variante | Comportament normal; restrângeți filtrul la variantele dorite, dacă e nevoie |

## 10. Capturi de ecran

Fișa este, deocamdată, **doar text**: nu are capturi de ecran. Capturile planificate, în ordinea
pașilor din secțiunea 6:

1. `01_liste_produse.png` — lista „Listă produse” din meniul Vânzări.
2. `02_lista_formular_filtru.png` — formularul listei „Electrocasnice — feed eMAG”, cu filtrul și limita.
3. `03_lista_arhivata.png` — o listă arhivată, cu banda „Arhivat”.

Ele se pot genera ulterior cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în limba română, după care se leagă în pașii din
secțiunea 6.

## 11. Observații pentru manual

Prezentați lista ca o **regulă**, nu ca o colecție de produse: utilizatorul spune „ce fel de
produse” și Odoo le găsește la fiecare folosire. În manualul unui client cu feed-uri, descrieți
lista împreună cu `deltatech_feed`, pentru că acolo se văd efectele ei (produsele trimise pe
platforme). Menționați limita implicită de 80, care surprinde des la prima generare a unui feed.
