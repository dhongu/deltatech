# Fișă Modul: Dimensiunile produsului și calculul volumului

**Modul:** `deltatech_product_dimension`
**Utilizator principal:** Responsabil de nomenclator (completează fișele produselor), logistică /
expediții (folosește volumul la transport și depozitare)
**Prioritate:** 🟢 Scăzută (date de nomenclator, fără efect contabil)

---

## 1. Scop business

Pentru transport, depozitare și ofertele de livrare, firma trebuie să știe cât loc ocupă un produs.
Odoo are pe produs doar **Volum**, pe care operatorul îl calculează de mână din dimensiunile cutiei.
Modulul adaugă pe fișa produsului rândul **Dimensiune**: lungime × lățime × înălțime, în
centimetri, și calculează singur **Volumul** din ele, în metri cubi. Dimensiunile rămân pe produs și
pot fi folosite de alte module (de exemplu, la transport sau la feed-uri pentru marketplace-uri).

## 2. Bază legală și context

- Modulul **nu are efect fiscal sau contabil**: nu creează documente și nu modifică stocul.
- Dimensiunile și volumul sunt date de nomenclator. Volumul se folosește în Odoo standard la
  transferuri și la calculele de transport; masa (greutatea) rămâne un câmp separat, completat
  manual.

## 3. Utilizatori și roluri

| Rol | Ce poate face |
|---|---|
| **Produse: Creează** (în **Date de bază**) | completează dimensiunile pe produs |
| Orice utilizator intern | vede dimensiunile și volumul produsului |

Roluri recomandate pentru testare:
- un **responsabil de nomenclator** (Produse: Creează), care completează dimensiunile.

## 4. Conturi și date implicate

Modulul **nu generează note contabile** și nu atinge conturi. Date minime pentru demo:

| Produs | Lungime | Lățime | Înălțime | Volum calculat |
|---|---|---|---|---|
| Cutie carton 40×30×25 | 40 cm | 30 cm | 25 cm | 0,03 m³ |
| Palet ambalat | 120 cm | 80 cm | 100 cm | 0,96 m³ |

Ambele produse sunt de tip **Bunuri**.

## 5. Configurare inițială

1. Instalați `deltatech_product_dimension` (dependență: `product`). Toate produsele existente
   primesc dimensiunile implicite **1 × 1 × 1** cm; volumul lor existent nu se schimbă.
2. Verificați în **Setări → Configurări generale**, blocul **Unități de măsură**, că la **Volum** este
   ales **Metri Cubi (m³)**. Calculul modulului dă întotdeauna metri cubi (secțiunea 9).

## 6. Flux de utilizare

### Pasul 1 — Completarea dimensiunilor pe produs

Deschideți produsul din **Vânzări → Produse → Produse** sau **Inventar → Produse → Produse** (de
exemplu „Cutie carton 40×30×25”) și mergeți în fila **Inventar**. În grupul **Logistică**, deasupra
rândului **Volum**, apare rândul **Dimensiune**, cu trei câmpuri: **Lungime** × **Latime** ×
**Inaltime** (etichetele sunt traduse fără diacritice), urmate de „cm”. Completați 40, 30 și 25.

Fila **Inventar** și grupul **Logistică** apar doar la produsele de tip **Bunuri**; la servicii și
combo-uri dimensiunile nu se afișează. Dimensiunile sunt ale produsului, nu ale variantei: la un
produs cu variante (mărimi, culori), toate variantele primesc aceleași dimensiuni și același volum.

### Pasul 2 — Volumul calculat

Imediat ce modificați una dintre dimensiuni, **Volum** se recalculează: lungime × lățime × înălțime
/ 1.000.000. Pentru cutia din exemplu: 40 × 30 × 25 = 30.000 cm³ = **0,03 m³**. Salvați produsul.

**Verificați:**
- **Volum** este 0,03 și unitatea afișată lângă el este m³;
- la paletul din exemplu, 120 × 80 × 100 dă **0,96 m³**;
- dacă una dintre dimensiuni este 0, volumul **nu** se recalculează și rămâne valoarea anterioară.

Volumul se poate corecta în continuare manual; o nouă modificare a dimensiunilor îl recalculează
din nou.

### Note de monografie și raportare

Modulul **nu înregistrează nicio notă contabilă** și nu adaugă rapoarte. Dimensiunile se pot afișa
în lista de produse sau exporta din **Acțiune → Export**, ca orice alt câmp al produsului.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux |
|---|---|
| `product` | fișa produsului, fila **Inventar** cu grupul **Logistică**, câmpul **Volum** și unitatea lui de măsură |
| `stock`, `delivery` (dacă sunt instalate) | folosesc volumul produsului la transferuri și la transport |

Ce este automat: volumul, la orice modificare a dimensiunilor din fișa produsului.

Ce rămâne manual: completarea dimensiunilor pentru fiecare produs, masa produsului și corectarea
volumului când produsul nu are formă de cutie.

## 8. Verificări pentru consultant

- [ ] Fila **Inventar** a unui produs de tip **Bunuri** are rândul **Dimensiune** (Lungime × Latime
      × Inaltime, în cm), deasupra lui **Volum**.
- [ ] Un produs nou are dimensiunile 1 × 1 × 1.
- [ ] Cutia 40 × 30 × 25 cm are volumul 0,03 m³ după completarea dimensiunilor.
- [ ] Cu o dimensiune 0, volumul nu se modifică.
- [ ] În **Setări → Configurări generale → Unități de măsură**, **Volum** este **Metri Cubi (m³)**.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Rândul **Dimensiune** nu apare | Produsul este de tip **Serviciu** sau **Combo** | Dimensiunile se completează doar la **Bunuri** |
| Volumul nu se schimbă după completarea dimensiunilor | Una dintre dimensiuni este 0, sau valorile au fost scrise prin import | Completați toate trei dimensiunile în formular; după un import, calculați volumul separat |
| Volumul pare de 35 de ori prea mic | La **Volum** este aleasă unitatea **Picioare Cubice (ft³)**, iar modulul calculează în m³ | Folosiți metri cubi sau corectați volumul manual |
| Volumul are prea puține zecimale (ex. 0,00 la o cutie mică) | Precizia zecimală a volumului este prea mică pentru produsele mici | Măriți precizia **Volume** în **Setări → Tehnic → Structura bazei de date → Exactitate zecimală** (mod dezvoltator) |

## 10. Capturi de ecran

Fișa este, deocamdată, **doar text**: nu are capturi de ecran. Capturile planificate, în ordinea
pașilor din secțiunea 6:

1. `01_produs_dimensiuni.png` — fila „Inventar” a produsului, cu rândul „Dimensiune” completat.
2. `02_volum_calculat.png` — volumul 0,03 m³ calculat din dimensiuni.

Ele se pot genera ulterior cu skill-ul `fisa-screenshots` (test `tests/test_screenshots.py`, mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`), în limba română, după care se leagă în pașii din
secțiunea 6.

## 11. Observații pentru manual

Prezentați dimensiunile ca date de nomenclator: se completează o dată, la crearea produsului, în
**centimetri**, iar volumul în m³ rezultă singur. Menționați că valorile implicite 1 × 1 × 1 nu sunt
reale și trebuie înlocuite. Pentru importurile masive de produse, recomandați includerea în fișier
atât a dimensiunilor, cât și a volumului, pentru că la import volumul nu se calculează.
