# Fișă Modul: Faze configurabile pe comenzile de achiziție

**Modul:** `deltatech_purchase_phase`
**Utilizator principal:** Operator achiziții, Responsabil aprovizionare
**Prioritate:** 🟢 Scăzută (vizibilitate suplimentară; nu schimbă fluxul standard al comenzii)

---

## 1. Scop business

Starea standard a unei comenzi de achiziție („CdO”, „CdO Trimisă”, „Comandă de achiziție”) nu spune
unde se află marfa după confirmare: dacă furnizorul a emis AWB-ul, dacă marfa e pe drum sau dacă a
ajuns. Modulul `deltatech_purchase_phase` adaugă pe comandă câmpul **Fază**, cu o listă de faze
configurabile (cu culori), afișat ca etichetă colorată pe formular și în listă. Faza se schimbă
automat la momentele-cheie (trimiterea cererii de ofertă, confirmarea comenzii, evoluția livrării)
și poate fi schimbată oricând manual. Fiecare schimbare rămâne în istoricul comenzii.

## 2. Bază legală și context

Nu există temei legal — este o funcționalitate de urmărire operațională a aprovizionării. Faza este
complementară stării standard a comenzii: nu o înlocuiește și nu blochează nicio operație.

## 3. Utilizatori și roluri

Operator achiziții, Responsabil aprovizionare, Manager achiziții.

Roluri recomandate pentru testare:
- Manager achiziții (grupul „Achiziții / Administrator”): creează, modifică și șterge fazele din
  configurare
- Utilizator achiziții: vede fazele, schimbă manual faza pe comandă și urmărește trecerile automate
- Utilizator intern oarecare: are doar drept de citire pe lista de faze

## 4. Conturi și date implicate

Modulul nu generează note contabile și nu folosește conturi.

Faze livrate implicit (cod tehnic → denumire afișată):

| Ordine | Cod | Denumire (RO) | Când se setează automat |
|---|---|---|---|
| 1 | `rfq` | Cerere de ofertă | la trimiterea cererii de ofertă (starea devine „CdO Trimisă”) |
| 2 | `purchase_confirm` | Confirmare achiziție | la confirmarea comenzii (starea devine „Comandă de achiziție”) |
| 3 | `pre_advice` | AWB Emis | când recepția legată primește starea de livrare „Avizat” (AWB generat) |
| 4 | `shipped` | Expediat | când recepția legată are starea de livrare „În tranzit”, „În depozit curier” sau „În livrare” |
| 5 | `delivered` | Livrat | când recepția legată primește starea de livrare „Livrat” |

Fazele 3–5 se schimbă automat numai dacă este instalat și modulul care urmărește starea livrării pe
transferuri (`deltatech_delivery_status`); fără el, aceste faze se setează manual.

Date minime pentru demo: un furnizor, un produs stocabil și o cerere de ofertă cu cel puțin o linie.

## 5. Configurare inițială

1. Instalați modulul `deltatech_purchase_phase` (depinde de `purchase_stock` și
   `deltatech_widget_many2one_badge`, care afișează faza ca etichetă colorată).
2. Accesați **Achiziții → Configurare → Purchase Order Phase**. Lista arată fazele livrate implicit.
3. Ajustați fazele după nevoie: în formular completați **Nume** (textul afișat utilizatorilor),
   **Secvență**, **Cod** (cheia tehnică folosită de trecerile automate) și **Culoare**. Ordinea se
   poate schimba și prin tragere în listă.
4. Nu modificați **Codul** fazelor livrate implicit (`rfq`, `purchase_confirm`, `pre_advice`,
   `shipped`, `delivered`) dacă vreți ca trecerile automate să le folosească în continuare. Dacă
   un cod lipsește, modulul creează automat o fază nouă cu numele egal cu codul.

## 6. Flux de utilizare

### Pasul 1 — Vizualizarea fazelor configurate

Accesați **Achiziții → Configurare → Purchase Order Phase**. Lista arată, în ordinea secvenței,
**Nume** și **Cod** pentru fiecare fază. Deschideți o fază pentru a vedea și culoarea aleasă —
aceasta este culoarea etichetei de pe comenzi.

### Pasul 2 — Trimiterea cererii de ofertă: faza „Cerere de ofertă”

Accesați **Achiziții → Comenzi → Cereri de ofertă**, deschideți o cerere de ofertă și trimiteți-o
furnizorului (**Trimite prin e-mail**). Când starea devine „CdO Trimisă”, câmpul **Fază** din antetul
formularului (în primul grup de câmpuri) se completează automat cu **Cerere de ofertă**, afișat ca
etichetă colorată.

### Pasul 3 — Confirmarea comenzii: faza „Confirmare achiziție”

Pe aceeași comandă, apăsați **Confirmă comanda**. Starea devine „Comandă de achiziție”, iar
**Fază** trece automat în **Confirmare achiziție**. În istoricul comenzii (chatter) apare
schimbarea câmpului Fază, cu valoarea veche și cea nouă.

### Pasul 4 — Evoluția livrării: fazele „AWB Emis”, „Expediat”, „Livrat”

Dacă este instalat modulul de stare a livrării pe transferuri, actualizarea câmpului **Stare livrare** pe
recepția legată de comandă mută automat faza comenzii:
- „Avizat” (AWB generat) pe recepție → faza **AWB Emis**;
- „În tranzit”, „În depozit curier” sau „În livrare” → faza **Expediat**;
- „Livrat” → faza **Livrat**;
- „Refuzat” → faza „refused” (creată automat la prima folosire; redenumiți-o în configurare, de ex.
  „Refuzat”).

Fără acel modul, setați aceste faze manual (pasul 5).

### Pasul 5 — Schimbarea manuală a fazei

Pe formularul comenzii, faceți clic pe câmpul **Fază** și alegeți altă fază din listă. Salvați.
Schimbarea apare în istoricul comenzii. O schimbare manuală nu blochează trecerile automate
ulterioare: la următorul eveniment (de ex. confirmarea), faza va fi suprascrisă automat.

### Pasul 6 — Urmărirea fazelor în listă

În **Achiziții → Comenzi → Comenzi de achiziție**, coloana **Fază** apare ca etichetă colorată pe
fiecare comandă. Pentru o imagine de ansamblu:
1. **Găsiți** coloana Fază la dreapta listei; culoarea etichetei identifică faza dintr-o privire.
2. **Verificați** că fiecare comandă confirmată are cel puțin faza „Confirmare achiziție” și că
   nicio comandă livrată nu a rămas într-o fază anterioară (ex. „Expediat”).
3. **Treceți mai departe** — grupați lista după Fază (din căutare: **Grupează după → Adaugă grupare
   personalizată → Fază**) pentru a vedea câte comenzi sunt în fiecare etapă.

### Note de monografie și raportare

Modulul nu generează note contabile. Faza este un câmp informativ de urmărire, independent de starea
comenzii, de recepție și de facturare.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `purchase_stock` | comenzile de achiziție și recepțiile legate de ele | dependență (manifest) |
| `deltatech_widget_many2one_badge` | afișarea fazei ca etichetă colorată | dependență (manifest) |
| `deltatech_delivery_status` | starea livrării pe transfer, care declanșează fazele „AWB Emis”, „Expediat”, „Livrat” | opțional (nu e dependență) |

Ce este automat: fazele „Cerere de ofertă” și „Confirmare achiziție”; fazele de livrare, dacă starea
livrării se urmărește pe recepție; crearea unei faze lipsă după cod; istoricul schimbărilor.
Ce rămâne manual: configurarea fazelor (nume, culori, ordine) și setarea fazelor care nu au eveniment
automat.

## 8. Verificări pentru consultant

- [ ] Meniul **Achiziții → Configurare → Purchase Order Phase** există și arată cele 5 faze implicite.
- [ ] Un utilizator fără drept de administrator pe achiziții vede fazele, dar nu le poate modifica.
- [ ] Trimiterea unei cereri de ofertă setează faza „Cerere de ofertă”.
- [ ] Confirmarea comenzii setează faza „Confirmare achiziție”.
- [ ] Fiecare schimbare de fază apare în istoricul comenzii, cu valoarea veche și cea nouă.
- [ ] Faza se poate schimba manual pe formular.
- [ ] Coloana **Fază** apare în lista comenzilor, colorată conform configurării.
- [ ] O comandă duplicată pornește fără fază (faza nu se copiază).
- [ ] Cu modulul de stare a livrării instalat: „Livrat” pe recepție mută comanda în faza „Livrat”.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| Faza nu se schimbă la trimitere/confirmare | Codul fazei a fost modificat în configurare, iar modulul a creat o fază nouă cu numele egal cu codul | Restabiliți codul `rfq` / `purchase_confirm` pe faza dorită și ștergeți faza creată automat |
| Apare o fază cu nume tehnic (ex. „refused”) | Fază creată automat, pentru că nu exista una cu acel cod | Redenumiți faza în configurare (câmpul Nume) |
| Fazele de livrare nu se schimbă singure | Starea livrării nu este urmărită pe recepție (modulul de stare a livrării lipsește) sau recepția nu e legată de comandă | Setați faza manual sau instalați modulul de stare a livrării |
| Nu pot crea/modifica faze | Utilizatorul nu are grupul „Achiziții / Administrator” | Acordați grupul de administrator pe achiziții |

## 10. Capturi de ecran

Fișa este **doar text** — nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele prin
etichetele lor reale din interfață. Dacă se decide ulterior completarea cu capturi, se rulează
skill-ul `fisa-screenshots`, care generează imaginile din `tests/test_screenshots.py` (mixinul
`ScreenshotCase`), în română, iar secțiunile 6 și 10 se actualizează în consecință.

## 11. Observații pentru manual

Prezentați faza ca „unde se află marfa”, complementar stării comenzii. Explicați că fazele de
livrare depind de urmărirea stării livrării pe recepție și, în lipsa ei, se setează manual. Meniul de
configurare apare în interfață cu eticheta „Purchase Order Phase” (netradusă). Avertizați
administratorul să nu schimbe codurile fazelor implicite.
