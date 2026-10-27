# Fișă Modul: Trimiterea mai multor comenzi de achiziție într-un singur e-mail, cu rezumat XLSX

**Modul:** `deltatech_purchase_mail`
**Utilizator principal:** Operator achiziții
**Prioritate:** 🟡 Medie (economisește timp la volume mari de comenzi, fluxul standard rămâne disponibil)

---

## 1. Scop business

Când un furnizor primește zilnic mai multe comenzi, trimiterea lor una câte una („Trimite prin
e-mail” de pe fiecare comandă) înseamnă multe e-mailuri separate și mult timp pierdut. Modulul
`deltatech_purchase_mail` permite selectarea mai multor comenzi de achiziție ale aceluiași furnizor
din listă și trimiterea lor **într-un singur e-mail**, care conține:

- un fișier **XLSX** de rezumat, cu toate liniile tuturor comenzilor selectate (comandă, cod produs,
  descriere, cantitate, preț);
- **PDF-ul oficial** al fiecărei comenzi, ca atașament separat.

După trimitere, fiecare comandă primește în istoric o notă cu e-mailul trimis, iar cererile de
ofertă trec în starea „CdO Trimisă”, exact ca la trimiterea standard.

## 2. Bază legală și context

Nu există temei legal specific — este o funcționalitate operațională de comunicare cu furnizorii.
Comanda de achiziție transmisă furnizorului rămâne documentul comercial standard Odoo (PDF-ul
raportului „Comandă de achiziție”); rezumatul XLSX este doar un document de lucru.

## 3. Utilizatori și roluri

Operator achiziții (utilizator intern cu drept de lucru pe comenzile de achiziție).

Roluri recomandate pentru testare:
- Administrator funcțional: instalează modulul și, dacă e nevoie, adaptează șablonul de e-mail
- Utilizator achiziții: selectează comenzile, trimite e-mailul, verifică istoricul comenzilor
- Furnizor (cutie de e-mail de test): verifică e-mailul primit și atașamentele

## 4. Conturi și date implicate

Modulul nu generează note contabile și nu folosește conturi.

Date minime pentru demo:
- un furnizor cu adresă de e-mail completată
- cel puțin două comenzi de achiziție (cereri de ofertă sau comenzi confirmate) pentru acel furnizor,
  fiecare cu cel puțin o linie de produs
- un server de e-mail de ieșire configurat (sau o bază de test în care e-mailurile rămân în coadă)

## 5. Configurare inițială

1. Instalați modulul `deltatech_purchase_mail` (depinde de `purchase` și `mail`).
2. Verificați că furnizorul are completat câmpul **E-mail** pe fișa de contact — fără el e-mailul
   nu poate fi pregătit.
3. Opțional, adaptați textul șablonului **„Comenzi de achiziție: trimite cu XLSX”** din
   **Setări → Tehnic → E-mail → Șabloane** (modul dezvoltator). Șablonul este încărcat o singură
   dată; modificările dumneavoastră nu sunt suprascrise la actualizarea modulului.
4. Nu sunt necesare alte setări, meniuri sau grupuri noi.

## 6. Flux de utilizare

### Pasul 1 — Selectarea comenzilor din listă

Accesați **Achiziții → Comenzi → Comenzi de achiziție** (sau **Achiziții → Comenzi → Cereri de
ofertă**). În vizualizarea listă, bifați căsuțele comenzilor care trebuie trimise. Toate comenzile
selectate trebuie să aibă **același furnizor**.

### Pasul 2 — Lansarea acțiunii „Trimite email”

Cu comenzile bifate, deschideți meniul **Acțiuni** (rotița din bara listei) și alegeți
**Trimite email**. Modulul pregătește în fundal:
- fișierul `purchase_orders_<dată>_<oră>.xlsx`, cu foaia „Purchase Orders” și coloanele
  „Comandă”, „Cod produs”, „Descriere produs”, „Cantitate”, „Preț” (prețul unitar fără TVA);
- câte un PDF pentru fiecare comandă, cu numele comenzii (ex. `P00012.pdf`).

Dacă comenzile aparțin unor furnizori diferiți sau furnizorul nu are e-mail, apare mesajul
„Trebuie să selectați exact un furnizor căruia să îi trimiteți e-mailul.” și nu se deschide nimic.

### Pasul 3 — Verificarea e-mailului în fereastra „Compune e-mail”

Se deschide fereastra standard **Compune e-mail**, precompletată:
- **Destinatari:** furnizorul comenzilor, cu adresa lui de e-mail;
- **Subiect:** „Purchase Orders” (textul din șablon, poate fi modificat aici);
- **Corp:** un mesaj cu lista comenzilor (număr comandă — furnizor);
- **Atașamente:** fișierul XLSX de rezumat și PDF-urile tuturor comenzilor selectate.

Înainte de trimitere, verificați pe ecran:
1. **Găsiți** zona de atașamente de sub corpul mesajului: trebuie să existe exact un fișier `.xlsx`
   și câte un `.pdf` pentru fiecare comandă bifată.
2. **Verificați** că numărul de PDF-uri este egal cu numărul de comenzi selectate și că lista din
   corpul e-mailului conține aceleași numere de comandă. Puteți descărca fișierul XLSX din atașament
   ca să controlați liniile și prețurile înainte de trimitere.
3. **Treceți mai departe** — adăugați, dacă e nevoie, alți destinatari sau text suplimentar, apoi
   apăsați **Trimite**.

Dacă închideți fereastra fără să trimiteți, nu se întâmplă nimic: comenzile nu sunt marcate ca
trimise și nu apare nicio notă în istoric.

### Pasul 4 — Verificarea istoricului pe fiecare comandă

După trimitere, deschideți oricare dintre comenzile selectate. În chatter (istoricul comenzii)
apare o notă cu subiectul și textul e-mailului trimis, cu atașamentele relevante pentru acea comandă:
rezumatul XLSX și **doar** PDF-ul comenzii respective (nu și PDF-urile celorlalte comenzi).
Cererile de ofertă aflate în starea „CdO” trec în starea **„CdO Trimisă”**, ca la trimiterea
standard.

### Note de monografie și raportare

Modulul nu generează note contabile. Este o funcționalitate de comunicare: nu schimbă cantități,
prețuri sau stări de facturare, ci doar starea cererii de ofertă („CdO” → „CdO Trimisă”), la fel ca
butonul standard „Trimite prin e-mail”.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `purchase` | comenzile de achiziție și raportul PDF „Comandă de achiziție” | dependență (manifest) |
| `mail` | fereastra de compunere, șablonul de e-mail și istoricul (chatter) | dependență (manifest) |

Ce este automat: generarea rezumatului XLSX, atașarea PDF-urilor, precompletarea destinatarului,
nota în istoricul fiecărei comenzi și marcarea cererilor de ofertă ca trimise.
Ce rămâne manual: selecția comenzilor, verificarea atașamentelor și apăsarea butonului **Trimite**.

## 8. Verificări pentru consultant

- [ ] Acțiunea **Trimite email** apare în meniul **Acțiuni** al listei de comenzi de achiziție
      (nu și pe formularul unei singure comenzi).
- [ ] Cu două sau mai multe comenzi ale aceluiași furnizor (cu e-mail), se deschide fereastra
      **Compune e-mail** cu furnizorul ca destinatar.
- [ ] Atașamentele conțin un singur fișier XLSX și câte un PDF pentru fiecare comandă selectată.
- [ ] Fișierul XLSX are coloanele „Comandă”, „Cod produs”, „Descriere produs”, „Cantitate”, „Preț”
      și câte un rând pentru fiecare linie a fiecărei comenzi.
- [ ] Cu comenzi de la furnizori diferiți apare mesajul „Trebuie să selectați exact un furnizor…”.
- [ ] Închiderea ferestrei fără trimitere nu lasă nicio notă și nu schimbă starea comenzilor.
- [ ] După **Trimite**, fiecare comandă are în istoric nota cu XLSX-ul și propriul PDF.
- [ ] Cererile de ofertă trimise au trecut în starea „CdO Trimisă”.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| „Trebuie să selectați exact un furnizor căruia să îi trimiteți e-mailul.” | Comenzile selectate au furnizori diferiți **sau** furnizorul unic nu are adresă de e-mail | Selectați doar comenzile unui furnizor; completați câmpul **E-mail** pe fișa furnizorului |
| „XlsxWriter este necesar pentru a genera fișiere XLSX.” | Biblioteca Python `xlsxwriter` lipsește pe server | Instalarea bibliotecii de către administratorul serverului |
| E-mailul nu ajunge la furnizor deși comenzile apar ca trimise | Serverul de e-mail de ieșire nu este configurat sau e-mailul a rămas în coadă | Verificați configurarea serverului de e-mail de ieșire și coada de e-mailuri |
| Acțiunea „Trimite email” nu apare | Sunteți pe formularul unei comenzi, nu în listă | Reveniți la lista de comenzi și bifați comenzile |

## 10. Capturi de ecran

Fișa este **doar text** — nu are capturi de ecran. Pașii din secțiunea 6 descriu ecranele prin
etichetele lor reale din interfață. Dacă se decide ulterior completarea cu capturi, se rulează
skill-ul `fisa-screenshots`, care generează imaginile din `tests/test_screenshots.py` (mixinul
`ScreenshotCase`), în română, iar secțiunile 6 și 10 se actualizează în consecință.

## 11. Observații pentru manual

Prezentați modulul ca o scurtătură pentru furnizorii cu multe comenzi: „bifați comenzile, Acțiuni →
Trimite email, verificați atașamentele, Trimite”. Subliniați condiția „un singur furnizor, cu e-mail”
și faptul că fiecare comandă păstrează în istoric dovada trimiterii, cu propriul PDF. Textul
e-mailului vine din șablonul „Comenzi de achiziție: trimite cu XLSX”, care poate fi tradus sau
adaptat de administrator.
