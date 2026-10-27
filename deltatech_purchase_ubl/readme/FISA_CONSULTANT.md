# Fișă Modul: Importul facturii de furnizor UBL (e-Factura) pe comanda de achiziție

**Modul:** `deltatech_purchase_ubl`
**Utilizator principal:** Operator achiziții, Contabil furnizori
**Prioritate:** 🔴 Ridicată (atinge prețurile de achiziție, recepția în stoc și factura furnizorului)

---

## 1. Scop business

Furnizorii din România transmit facturile în format XML UBL (e-Factura, prin SPV). Reintroducerea
manuală a liniilor pe comanda de achiziție, actualizarea prețurilor furnizorului, validarea recepției
și crearea facturii sunt operații repetitive, cu risc de greșeală. Modulul `deltatech_purchase_ubl`
citește fișierul XML al facturii și, pornind de la comanda de achiziție:

- identifică automat produsele (după cod de bare, cod furnizor, cod intern sau denumire exactă) și
  arată, înainte de import, cum a asociat fiecare linie (verde / galben / roșu);
- actualizează liniile comenzii (cantitate, preț, discount) și adaugă liniile lipsă;
- actualizează prețurile din lista de prețuri a furnizorului;
- opțional, setează cantitățile pe recepție și o validează;
- creează factura furnizorului din comandă, cu numărul, data și scadența din XML;
- compară totalul comenzii cu factura, fără TVA și cu TVA, și avertizează la diferențe;
- avertizează când cota de TVA a unei linii de comandă diferă de cea din factură.

Când XML-ul este atașat automat pe comandă (de ex. de fluxul de preluare din SPV), importul rulează
singur, iar dacă ceva nu se potrivește, cumpărătorul primește o activitate „Import SPV necesită
verificare”.

## 2. Bază legală și context

Formatul importat este factura electronică UBL 2.1 folosită în sistemul național RO e-Factura
(standardul CIUS-RO). Modulul nu transmite și nu descarcă nimic din SPV; doar citește un fișier XML
deja primit. Obligațiile privind e-Factura rămân acoperite de modulele de localizare; acest modul
este un instrument operațional care preia datele facturii în fluxul de achiziții.

## 3. Utilizatori și roluri

Operator achiziții, Contabil furnizori, Gestionar (recepții).

Roluri recomandate pentru testare:
- Utilizator achiziții: lansează importul de pe comandă, verifică previzualizarea, confirmă importul
- Gestionar: verifică recepția validată din XML (cantități, stare)
- Contabil furnizori: verifică factura creată (număr, dată, scadență, taxe) și o validează

## 4. Conturi și date implicate

Modulul nu definește conturi noi. Factura furnizorului este creată cu mecanismul standard al comenzii
de achiziție („Creează factură”), deci folosește jurnalul de achiziții, contul furnizorului (401) și
conturile de stoc/cheltuieli și TVA configurate pe produse și taxe.

Date minime pentru demo:
- un furnizor cu **CUI** (codul fiscal din XML trebuie să corespundă) și, ideal, cu prețuri de
  furnizor având **Cod produs furnizor** completat
- produse stocabile cu cod de bare sau cod intern
- o comandă de achiziție **confirmată** pentru furnizor (pentru recepție și factură)
- un fișier XML UBL de factură de la furnizor, cu referința comenzii (`OrderReference`) completată,
  dacă se dorește identificarea automată a comenzii

## 5. Configurare inițială

1. Instalați modulul `deltatech_purchase_ubl` (depinde de `purchase_stock` și `account`).
2. Pe prețurile furnizorului (**Achiziții → Produse → Produse**, tab **Achiziție**), completați
   **Cod produs furnizor**, pentru ca asocierea să se facă după cod (linie verde), nu după nume.
3. Verificați că furnizorul are CUI-ul completat; fără comandă în context, furnizorul se caută după
   CUI și apoi după denumire.
4. Importul automat la atașarea unui XML pe comandă este activ implicit. Se poate dezactiva prin
   parametrul de sistem `deltatech_purchase_ubl.auto_import` = `False`
   (**Setări → Tehnic → Parametri → Parametri de sistem**, modul dezvoltator).

## 6. Flux de utilizare

### Pasul 1 — Deschiderea asistentului de import de pe comandă

Accesați **Achiziții → Comenzi → Comenzi de achiziție** și deschideți comanda furnizorului. În bara
de sus apăsați **Import factură**. Se deschide fereastra **Import factură**. Dacă pe comandă este deja
atașat un fișier XML de factură UBL, acesta este preluat automat în câmpul **Fișier XML**.

### Pasul 2 — Alegerea fișierului și a opțiunilor

În grupul **Fișier**, încărcați factura în câmpul **Fișier XML** (dacă nu a fost preluată automat);
câmpul **Comandă de achiziție** arată comanda pe care se face importul. În grupul **Opțiuni**:
- **Actualizează prețurile furnizorului** (bifat implicit) — scrie prețul unitar din XML în lista de
  prețuri a furnizorului;
- **Creează factură furnizor** (bifat implicit) — creează factura furnizorului din comandă;
- **Validează recepția din XML** (nebifat implicit) — setează cantitățile din XML pe recepția
  comenzii și o validează.

Deasupra pot apărea avertismente galbene:
- un avertisment că **comanda are deja linii** — liniile existente vor fi actualizate; atenție, în
  versiunea curentă textul afirmă că liniile noi nu se adaugă, dar importul **le adaugă**
  (vezi [dhongu/deltatech#3820](https://github.com/dhongu/deltatech/issues/3820));
- un avertisment de **verificare a totalului**, dacă valoarea fără TVA sau totalul cu TVA al
  comenzii diferă de cel din XML (câte un rând pentru fiecare diferență).

Apăsați **Previzualizare**.

### Pasul 3 — Verificarea asocierii produselor în previzualizare

Fereastra afișează un tabel cu câte un rând pentru fiecare linie a facturii: **Cod furnizor**,
**Descriere furnizor**, **Cantitate**, **Preț unitar**, **Produs** (produsul găsit), **Acțiune** și
**Tip potrivire**.

1. **Găsiți pe ecran** culoarea fiecărui rând și coloana **Tip potrivire**:
   - **verde** — „După cod furnizor” sau „După cod de bare”: asociere sigură;
   - **galben** — „După nume”: asociere doar după denumire, trebuie verificată;
   - **roșu** — „Negăsit”: niciun produs găsit.
2. **Verificați** fiecare rând galben și roșu: produsul din coloana **Produs** este cel facturat?
   Cantitatea și prețul unitar corespund facturii? Pentru un rând greșit alegeți alt produs în
   coloana **Produs** (Tip potrivire devine „Ales manual”). Pentru un rând roșu alegeți în coloana
   **Acțiune**: un produs existent („Folosește produsul”), **Creează produs nou** (se creează un
   produs stocabil nou, cu prețul de furnizor din XML) sau **Ignoră** (linia nu se importă).
3. **Treceți mai departe** — reverificați bifele **Actualizează prețurile furnizorului**,
   **Creează factură furnizor**, **Validează recepția din XML** de sub tabel și apăsați **Importă**.

### Pasul 4 — Citirea rezultatului importului

Fereastra trece în secțiunea **Rezultat**, cu un jurnal colorat (verde = operații reușite,
portocaliu/roșu = avertismente):
- „Furnizor: …” și „Comandă: … | Referință XML: …”;
- câte linii de comandă au fost actualizate și câte au fost adăugate;
- produsele create și prețurile actualizate;
- „Recepție actualizată: …” sau un avertisment că recepția nu a putut fi validată;
- „Factură furnizor creată: …” sau motivul pentru care nu a fost creată (comandă neconfirmată, nimic
  de facturat, factură existentă deja cu aceeași referință);
- rezultatul verificării totalului comenzii față de XML (fără TVA și cu TVA);
- un avertisment „VAT rate differs on … line(s) …” când cota de TVA a liniilor de comandă diferă de
  cea din factură — de obicei lipsește poziția fiscală a furnizorului (achiziție intracomunitară cu
  taxare inversă sau import);
- dacă comanda fusese creată goală din butonul de încărcare al listei de achiziții, cu compania sau
  utilizatorul ca furnizor: „Furnizorul comenzii a fost luat din document: …”.

Citiți jurnalul înainte de a închide: orice rând roșu cere o verificare manuală pe comandă.

### Pasul 5 — Verificarea comenzii și a recepției

Apăsați **Deschide comanda de achiziție**. Pe comandă verificați liniile (cantități, prețuri unitare,
discounturi preluate din XML) și liniile noi adăugate. Dacă ați bifat **Validează recepția din XML**,
deschideți recepția din butonul **Recepție**: cantitățile realizate sunt cele din factură, iar
recepția este validată.

### Pasul 6 — Verificarea facturii furnizorului

Din fereastra de rezultat apăsați **Vezi factura furnizor** (sau deschideți-o din butonul
**Facturi furnizor** de pe comandă). Factura este în ciornă și are completate din XML: **Referință** (numărul
facturii furnizorului), **Data facturii**, **Data scadenței** și **Document sursă** (referința
comenzii din XML). Cotele de TVA ale liniilor sunt aliniate cu procentele din XML.
1. **Găsiți** totalul facturii și comparați-l cu totalul din XML-ul furnizorului.
2. **Verificați** că furnizorul, numărul și data sunt corecte și că fiecare linie are cota de TVA din
   factura primită (atenție la liniile cu 0% — vezi secțiunea 9).
3. **Treceți mai departe** — confirmați factura cu butonul standard **Confirmă**.

### Pasul 7 — Importul automat la atașarea XML-ului

Când un fișier XML de factură UBL este atașat automat pe comandă (de exemplu de fluxul de preluare a
facturilor din SPV), importul rulează fără fereastră: prețuri, linii, recepție și factură. Dacă
totalul nu se potrivește sau rămân linii neasociate, factura **nu** se creează, jurnalul colorat se
postează în istoricul comenzii, iar responsabilul comenzii primește activitatea
**„Import SPV necesită verificare”**. Rezolvați liniile pe comandă, apoi relansați importul manual
(pașii 1–6).

Dacă documentul XML este o **notă de credit**, nu se aplică pe comandă: jurnalul afișează
„Atenție: documentul … este o notă de credit; notele de credit nu se importă. Înregistrați manual
rambursarea de la furnizor.”

### Note de monografie și raportare

Modulul nu generează note contabile proprii. Notele rezultă din documentele standard create în flux:
- **Recepția validată** (în configurarea RO cu evaluare automată a stocului): Dr 371 „Mărfuri” (sau
  contul de stoc al categoriei) = Cr 408 „Furnizori — facturi nesosite”, la valoarea comenzii.
- **Factura furnizorului confirmată**: Dr 408 (pentru cantitățile recepționate) / Dr cont de
  cheltuială (pentru servicii) + Dr 4426 „TVA deductibilă” = Cr 401 „Furnizori”.

Conturile exacte depind de configurarea categoriilor de produse, a taxelor și a jurnalului de
achiziții.

## 7. Legături cu alte module / declarații

| Modul / proces | Rol în flux | Tip legătură |
|---|---|---|
| `purchase_stock` | comanda de achiziție, recepția și prețurile furnizorului | dependență (manifest) |
| `account` | factura furnizorului | dependență (manifest) |
| Preluarea facturilor din SPV (`l10n_ro_message_spv_purchase`) | atașează automat XML-ul pe comandă și declanșează importul automat | opțional |

Ce este automat: identificarea furnizorului și a comenzii din XML, asocierea produselor, actualizarea
liniilor și a prețurilor, adăugarea liniilor lipsă, validarea recepției (dacă e bifată), crearea
facturii, verificarea totalului, activitatea de verificare la importul automat.
Ce rămâne manual: verificarea rândurilor galbene/roșii în previzualizare, confirmarea facturii,
înregistrarea notelor de credit, rezolvarea liniilor neasociate la importul automat.

## 8. Verificări pentru consultant

- [ ] Butonul **Import factură** apare pe formularul comenzii de achiziție.
- [ ] Un XML atașat pe comandă este preluat automat în **Fișier XML** la deschiderea ferestrei.
- [ ] **Previzualizare** arată câte un rând pe linie de factură, colorat verde/galben/roșu după
      **Tip potrivire**.
- [ ] Schimbarea produsului pe un rând îl marchează „Ales manual”; „Ignoră” lasă linia neimportată.
- [ ] După **Importă**, liniile existente au cantitatea și prețul din XML, iar produsele care nu erau
      pe comandă apar ca linii noi.
- [ ] Prețul de furnizor (cu **Cod produs furnizor**) este actualizat pentru produsele importate.
- [ ] Cu **Validează recepția din XML** bifat, recepția comenzii este validată cu cantitățile din XML.
- [ ] Factura furnizorului are referința, data și scadența din XML; un al doilea import al aceleiași
      facturi nu creează o factură dublă.
- [ ] Pe o comandă neconfirmată, factura nu se creează și jurnalul explică motivul.
- [ ] Verificarea totalului apare în jurnal, pe valoarea fără TVA și pe totalul cu TVA.
- [ ] O linie cu altă cotă de TVA decât în factură produce avertismentul de cotă TVA.
- [ ] O notă de credit XML nu modifică comanda și este semnalată în jurnal.
- [ ] La importul automat cu linii neasociate apare activitatea „Import SPV necesită verificare”.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză probabilă | Remediere |
|-----------------|-----------------|-----------|
| „Vă rugăm să selectați un fișier XML.” | Câmpul **Fișier XML** este gol | Încărcați fișierul facturii |
| „XML nevalid: …” | Fișierul nu este un XML corect (de ex. PDF sau arhivă ZIP din SPV) | Extrageți fișierul XML al facturii și reîncercați |
| „No vendor found for supplier VAT … / name …” | Importul nu e pornit de pe o comandă, iar furnizorul nu există cu acel CUI/nume | Porniți importul de pe comandă sau creați furnizorul cu CUI-ul din XML |
| Multe rânduri galbene/roșii | Prețurile furnizorului nu au **Cod produs furnizor**, produsele nu au cod de bare | Completați codurile furnizorului; la importurile următoare asocierea va fi verde |
| „Crearea facturii de furnizor a fost sărită: comanda … nu este încă confirmată…” | Comanda este în stadiul de cerere de ofertă | Confirmați comanda și relansați importul |
| „Factura de furnizor nu a fost creată: pe comanda … nu a mai rămas nimic de facturat.” | Comanda e deja facturată sau se facturează pe cantități recepționate și nimic nu e recepționat | Verificați facturile existente; validați recepția (bifați **Validează recepția din XML**) |
| „Factura furnizor există deja pentru această referință de factură (…)” | Factura a fost deja importată | Nu e nevoie de acțiune; folosiți **Vezi factura furnizor** |
| „Atenție: recepția … nu a putut fi validată; verificați-o manual.” | Cantitățile nu pot fi setate (de ex. produs cu lot/serie) | Completați și validați recepția manual |
| „VAT rate differs on … line(s) …” | Furnizorul nu are poziția fiscală potrivită (intracomunitar / import), deci comanda a luat TVA-ul intern | Setați poziția fiscală pe furnizor și pe comandă, apoi creați factura |
| Total fără TVA corect, total cu TVA diferit | Cotele de TVA ale comenzii diferă de cele din factură | Verificați poziția fiscală și taxele liniilor |
| Factură XML în altă monedă decât comanda | Prețurile din XML se scriu în moneda comenzii, fără conversie | Importați doar pe o comandă în aceeași monedă ca factura |

## 10. Capturi de ecran

Fișa este **doar text** — pașii din secțiunea 6 nu includ capturi. În `readme/screenshots/` există
patru capturi generate automat din `tests/test_screenshots.py` (mixinul `ScreenshotCase` din
`l10n_ro_doc_screenshots`, import defensiv), care corespund pașilor 3, 4 și 7, dar nu sunt
încorporate în fișă:

1. `06_preview_linie_galbena.png` — previzualizarea cu o linie asociată doar după nume (galbenă).
2. `07_activitate_verificare.png` — activitatea „Import SPV necesită verificare” pe comandă.
3. `08_preview_actiune_linie.png` — alegerea acțiunii pe o linie din previzualizare.
4. `09_rezultat_deschide_comanda.png` — rezultatul importului, cu butonul de deschidere a comenzii.

Pentru o fișă completă cu capturi pe toți pașii se rulează skill-ul `fisa-screenshots`; regenerarea
capturilor existente:

```bash
./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_purchase_ubl,l10n_ro_doc_screenshots \
    --test-tags=fise_screenshots --stop-after-init
```

## 11. Observații pentru manual

Prezentați importul ca flux „comandă → Import factură → Previzualizare → Importă → verificare factură”
și insistați pe citirea culorilor din previzualizare: verde se poate accepta, galben se verifică,
roșu se decide (produs, produs nou sau ignorare). Recomandați completarea **Codului produs furnizor**
pe prețurile furnizorului, care face asocierea sigură. Pentru importul automat din SPV, explicați
activitatea „Import SPV necesită verificare” și faptul că factura nu se creează până la rezolvarea
liniilor. Explicați și avertismentul de cotă TVA, care trimite la poziția fiscală a furnizorului.
Avertismentul de cotă TVA apare momentan în engleză.
