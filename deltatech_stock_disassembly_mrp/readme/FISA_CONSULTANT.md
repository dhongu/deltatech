# Fișă Modul: Dezmembrare liberă completată din lista de materiale

**Modul:** `deltatech_stock_disassembly_mrp`
**Utilizator principal:** Gestionar / responsabil producție
**Prioritate:** 🟢 Scăzută (modul de legătură, instalat automat; scurtează completarea procesului-verbal)

---

## 1. Scop business

Modulul **Free Disassembly** (`deltatech_stock_disassembly`) permite dezmembrarea unui produs printr-un
proces-verbal de dezmembrare, fără listă de materiale și fără comandă de producție: produsele rezultate
se introduc de mână, rând cu rând. Când produsul dezmembrat are totuși o listă de materiale (de exemplu
un ansamblu care se desface înapoi în componente), introducerea manuală este repetitivă și predispusă
la greșeli.

Acest modul de legătură, instalat automat când există și **Free Disassembly**, și **Manufacturing**,
adaugă pe procesul-verbal câmpul **Bill of Materials** și butonul **Load from BoM**, care completează
produsele rezultate din componentele listei, în proporția ei. Procesul-verbal rămâne „liber”: rândurile
încărcate se pot modifica, șterge sau completa, iar repartizarea costului și contabilizarea sunt cele
ale procesului-verbal.

## 2. Bază legală și context

Baza legală și tratamentul contabil sunt cele ale modulului **Free Disassembly**: procesul-verbal de
dezmembrare este documentul justificativ al operațiunii (cu comisie și motiv), iar ieșirea produsului
dezmembrat și intrarea produselor rezultate se înregistrează la costul efectiv, conform OMFP 1802/2014.
Acest modul nu schimbă nimic din tratamentul contabil; doar propune rândurile.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Gestionar / responsabil producție | Creează procesul-verbal, alege lista de materiale, încarcă rândurile, le ajustează, validează |
| Contabil | Verifică nota contabilă a procesului-verbal |

Câmpul **Bill of Materials** este vizibil doar utilizatorilor cu rolul **Manufacturing / User**. Roluri
recomandate pentru testare: **Inventory / User** + **Manufacturing / User**.

## 4. Conturi și date implicate

Conturile sunt cele ale procesului-verbal de dezmembrare (vezi „Note de monografie”), după categoriile
produselor: de exemplu 371 „Mărfuri”, 301 „Materii prime”, 302 „Materiale consumabile”, 345 „Produse
finite”, 346 „Produse reziduale”, 711, 607.

Date minime pentru demo:

- un produs stocabil cu stoc în locația sursă (produsul de dezmembrat);
- o listă de materiale de tip normal pentru el, cu 2–3 componente stocabile, eventual o componentă de tip
  kit și un serviciu (ca să se vadă explodarea kitului și omiterea serviciului);
- costul produsului dezmembrat cunoscut (cost mediu sau FIFO).

## 5. Configurare inițială

1. Instalați **Free Disassembly** (`deltatech_stock_disassembly`) și **Manufacturing** (`mrp`); modulul
   `deltatech_stock_disassembly_mrp` se instalează automat.
2. Configurarea procesului-verbal (locații, metoda de repartizare, conturi) este cea a modulului **Free
   Disassembly**.
3. Verificați că produsul de dezmembrat are o listă de materiale de tip normal (**Manufacturing →
   Products → Bills of Materials**). Kiturile nu sunt propuse ca listă a procesului-verbal.

## 6. Flux de utilizare

### Pasul 1 — Crearea procesului-verbal

**Inventory → Operations → Adjustments → Disassembly → New**. În grupul **Disassembled Product** alegeți
produsul (și lotul, dacă e urmărit pe loturi), cantitatea și locația sursă.

Ce se întâmplă: câmpul **Bill of Materials**, sub locația sursă, se completează cu lista de materiale
normală a produsului (a variantei sau a șablonului), pentru compania procesului-verbal. Se poate alege
altă listă a aceluiași produs sau se poate goli câmpul.

### Pasul 2 — Încărcarea produselor rezultate

Cu procesul-verbal în ciornă și lista aleasă, apăsați **Load from BoM** și confirmați mesajul „The
product lines are replaced by the components of the bill of materials.”.

Ce se întâmplă:

- rândurile de tip **Product** din pagina **Results** se înlocuiesc cu componentele listei, pentru
  cantitatea dezmembrată convertită în unitatea listei (de exemplu, o listă pentru 1 bucată cu 4 roți dă,
  la 3 bucăți dezmembrate, 12 roți);
- componentele de tip kit sunt explodate până la componentele lor;
- serviciile și componentele cu cantitate zero sunt omise;
- rândurile de tip **Loss** (pierderi) rămân neschimbate.

Butonul nu apare dacă procesul-verbal nu este în ciornă sau nu are listă de materiale.

### Pasul 3 — Ajustarea și verificarea rândurilor

În pagina **Results** găsiți rândurile încărcate: produs, cantitate, unitate, lot, destinație. Verificați
că produsele și cantitățile corespund cu ce s-a obținut fizic din dezmembrare. Modificați cantitățile,
ștergeți componentele care nu s-au recuperat, adăugați loturile sau rândurile de pierderi, apoi alegeți
metoda de repartizare a costului (**Allocation Method**). Verificați că **Allocated** este egal cu
valoarea produsului dezmembrat.

### Pasul 4 — Validarea

Apăsați **Validate**. De aici, fluxul este cel al modulului **Free Disassembly**: produsul dezmembrat iese
din stoc la costul efectiv, produsele rezultate intră la valoarea repartizată și se generează o singură
notă contabilă pe procesul-verbal.

### Note de monografie și raportare

Modulul nu adaugă note contabile proprii; nota este cea a procesului-verbal **Free Disassembly**, în
jurnalul de stoc, la data procesului-verbal. Exemple, pe planul de conturi RO:

- dezmembrarea unei mărfi în mărfuri: Dr 371 „Mărfuri” (produse rezultate) / Cr 371 „Mărfuri” (produs
  dezmembrat), fără compensarea rândurilor pe același cont;
- rezultate înregistrate ca produse reziduale: Dr 346 „Produse reziduale” / Cr 711 „Venituri aferente
  costurilor stocurilor de produse”, iar produsul dezmembrat iese prin contul lui de cheltuieli (de
  exemplu Dr 607 / Cr 371);
- pierderi peste normă: Dr contul de cheltuieli al produsului dezmembrat (60x/607, după categorie) /
  Cr contul lui de stoc; cheltuiala este nedeductibilă, iar procesul-verbal amintește (în istoric și pe
  PDF) de ajustarea TVA dedusă.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `deltatech_stock_disassembly` | procesul-verbal de dezmembrare, repartizarea costului, nota contabilă |
| `mrp` | listele de materiale și explodarea kiturilor |

**Ce e automat:** propunerea listei de materiale după produs, completarea produselor rezultate din
componente în proporția listei, explodarea kiturilor, omiterea serviciilor, păstrarea rândurilor de
pierderi.

**Ce rămâne manual:** confirmarea rândurilor față de ce s-a obținut fizic, loturile, pierderile, metoda de
repartizare, validarea.

## 8. Verificări pentru consultant

- [ ] La alegerea produsului dezmembrat, **Bill of Materials** se completează cu lista lui normală.
- [ ] **Load from BoM** înlocuiește rândurile de tip **Product** cu componentele, la cantitatea
  dezmembrată × proporția listei.
- [ ] O componentă kit apare explodată în componentele ei; un serviciu nu apare.
- [ ] Rândurile de tip **Loss** rămân după încărcare.
- [ ] Butonul **Load from BoM** nu apare pe un proces-verbal validat sau fără listă.
- [ ] Rândurile încărcate se pot modifica și șterge înainte de validare.
- [ ] După validare, nota contabilă este cea a procesului-verbal, cu valoarea repartizată pe produsele
  rezultate.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `Only a draft disassembly report can be filled in.` | Încărcare pe un proces-verbal care nu mai este în ciornă | Readuceți-l în ciornă (dacă e anulat) sau creați unul nou |
| `Select a bill of materials.` | Câmpul **Bill of Materials** este gol | Alegeți o listă de materiale a produsului |
| Lista dorită nu apare la alegere | Lista este de tip kit sau aparține altui produs sau altei companii | Folosiți o listă de tip normal a produsului dezmembrat, în compania procesului-verbal |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița, bannerul și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`.
Dacă se doresc capturi, ele se generează cu skill-ul `fisa-screenshots` (procesul-verbal cu lista
propusă, confirmarea **Load from BoM**, rândurile încărcate, procesul-verbal validat) și se leagă apoi
în pașii din secțiunea 6.

## 11. Observații pentru manual

- Manualul procesului-verbal de dezmembrare poate prezenta **Load from BoM** ca o scurtătură opțională,
  nu ca un pas obligatoriu.
- De subliniat că rândurile încărcate sunt o propunere: procesul-verbal trebuie să reflecte ce s-a
  obținut efectiv, constatat de comisie.
