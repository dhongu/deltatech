# Fișă Modul: Tipuri de comenzi și facturi cu valori implicite

**Modul:** `deltatech_record_type`
**Utilizator principal:** Agenți de vânzări și achiziții, facturare; manager vânzări / achiziții (configurare)
**Prioritate:** 🟡 Medie (standardizează documentele pe tipuri de activitate și reduce erorile de completare)

---

## 1. Scop business

Firmele care lucrează pe mai multe fluxuri (de exemplu vânzare en-gros, retail, export, service) vor ca
fiecare comandă sau factură să fie marcată cu tipul ei și să fie completată la fel de fiecare dată.
Modulul adaugă **tipuri de înregistrare** pentru comenzile de vânzare, comenzile de achiziție și
facturi. Fiecare tip poate avea:

- **Valori implicite**: câmpuri ale documentului completate automat la alegerea tipului (lista de
  prețuri, jurnalul, termenul de plată, depozitul etc.);
- **Rute** de aprovizionare, folosite la liniile comenzilor de vânzare;
- **Utilizatori permiși**, la tipurile de comenzi de vânzare;
- o **Companie**, în mediile cu mai multe companii.

Opțional, confirmarea unei comenzi fără tip poate fi interzisă. Tipul apare și în listele și analizele
de vânzări și achiziții, ca dimensiune de grupare.

## 2. Bază legală și context

Modulul nu are bază legală proprie și nu modifică notele contabile generate de Odoo. Contextul este
organizatoric: separarea fluxurilor comerciale, completarea uniformă a documentelor și raportarea pe
tipuri. Indirect, prin valorile implicite (de exemplu **Jurnal**), tipul poate trimite facturile pe
jurnale (serii) diferite.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Manager vânzări / achiziții / contabil | Definește tipurile, valorile implicite, rutele și utilizatorii permiși |
| Administrator | Activează sau dezactivează confirmarea comenzilor fără tip |
| Agent de vânzări / achiziții | Alege tipul pe comandă; confirmă comanda |
| Facturare | Alege tipul pe factură |

Grupul **Poate confirma comenzi fără tip comandă** (*Can Confirm Orders Without Record Type*) permite
confirmarea comenzilor de vânzare și achiziție fără tip. Pentru testare: un administrator și un agent
de vânzări fără acest grup.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile proprii. Pentru demo sunt necesare:

- două tipuri de comandă de vânzare (de exemplu „En-gros” și „Retail”), cu valori implicite diferite
  (de exemplu **Listă de prețuri** sau **Termeni de plată**);
- un tip de comandă de achiziție și un tip de factură;
- doi agenți de vânzări, ca să se vadă efectul câmpului **Utilizatori permiși**;
- opțional, o rută de aprovizionare (de exemplu „Cumpărare” sau „Livrare directă”) pentru un tip de
  vânzare.

## 5. Configurare inițială

1. Instalați modulul `deltatech_record_type` (depinde de `sale`, `sale_stock`, `purchase`).
2. Tipurile de comandă de vânzare: **Vânzări → Configurare → Tipuri comandă**
   (*Sales → Configuration → Order Types*). Butonul **Nou** deschide formularul **Tip înregistrare**:
   - **Nume**; **Model** (completat automat cu **Comandă de vânzare**);
   - **Utilizatori permiși** — dacă e gol, tipul e disponibil tuturor; altfel, doar celor din listă;
   - **Rute** (vizibil cu rutele multi-pas activate în Inventar) — rutele propuse liniilor comenzii;
   - **Companie** — gol pentru toate companiile;
   - fila **Valori implicite**: pe fiecare rând alegeți **Câmp**, apoi valoarea:
     - pentru câmpurile de tip legătură (**Tip câmp** = `Id`), alegeți înregistrarea în coloana **Related**;
     - pentru text (**Tip câmp** = `Char`), scrieți valoarea în **Valoare câmp** între ghilimele
       simple, de exemplu `'export'` (valoarea este interpretată ca expresie);
     - pentru bifă (**Tip câmp** = `Boolean`), scrieți `True` sau `False`.
3. Tipurile de comandă de achiziție: **Achiziții → Configurare → Tipuri comandă**
   (*Purchase → Configuration → Order Types*), cu același formular.
4. Tipurile de factură: **Facturare → Configurare → Facturare → Tipuri factură**
   (*Invoicing → Configuration → Invoicing → Invoice Types*).
5. Regula de confirmare: **Setări → Vânzări**, blocul **Oferte și Comenzi**, opțiunea **Confirmat fără
   tip comandă** (*Confirmed without record type*). Este **bifată implicit**: toți utilizatorii pot
   confirma comenzi fără tip. Debifați-o ca să ceară tipul la confirmare; după debifare, dreptul
   **Poate confirma comenzi fără tip comandă** se acordă individual, din fișa utilizatorului (mod
   dezvoltator).

## 6. Flux de utilizare

### Pasul 1 — Comanda de vânzare cu tip

În **Vânzări → Comenzi → Oferte**, butonul **Nou**. Deasupra câmpului **Client** apare câmpul
**Tip comandă** (doar dacă există cel puțin un tip de comandă de vânzare). Lista propune tipurile fără
**Utilizatori permiși** și pe cele în care se află utilizatorul curent.

La alegerea tipului, câmpurile din **Valori implicite** se completează automat; ele pot fi modificate
apoi manual. Câmpul **Jurnal** (*Journal*) din fila **Alte informații**, ascuns în Odoo standard, este
afișat de modul și poate fi completat din valorile implicite, pentru ca factura să meargă pe jurnalul
dorit.

### Pasul 2 — Confirmarea comenzii

Apăsați **Confirmare**. Dacă opțiunea **Confirmat fără tip comandă** e debifată, utilizatorul nu are
dreptul **Poate confirma comenzi fără tip comandă**, iar comanda nu are tip, confirmarea este oprită
cu mesajul *You do not have the rights to confirm an order without specifying an Order Type.*

Nu sunt oprite: comenzile din magazinul online, cele acceptate sau semnate de client în portal și cele
confirmate prin plata online.

După confirmare, tipul nu mai poate fi schimbat. Liniile comenzii fără rută proprie primesc rutele
tipului, iar aprovizionarea (livrare, cumpărare, producție) urmează acele rute.

### Pasul 3 — Comanda de achiziție cu tip

În **Achiziții → Comenzi → Cereri de ofertă**, câmpul **Tip comandă** apare deasupra câmpului
**Furnizor**. La alegerea tipului se aplică valorile implicite. Pe comandă apare și câmpul **Jurnal**
(după **Poziție fiscală**, în fila **Alte informații**): factura de furnizor creată din comandă este
înregistrată pe acest jurnal. Regula de confirmare de la pasul 2 se aplică și la **Confirmare
comandă**. Tipul poate fi schimbat doar cât comanda este cerere de ofertă.

### Pasul 4 — Factura cu tip

Pe factura sau nota de credit de client, câmpul **Tip Factura** (*Invoice Type*) apare după
**Echipa de vânzări**, în fila **Alte informații** (grupul **Factură**), dacă există cel puțin un tip
de factură. Pe facturile de furnizor grupul nu este afișat, deci tipul nu se poate alege acolo. La
alegere se aplică valorile implicite. Tipul se poate schimba doar cât factura este ciornă. Facturile
nu au regulă de confirmare: o factură se poate posta și fără tip.

### Pasul 5 — Raportare pe tipuri

1. **Găsiți pe ecran** — în listele de comenzi de vânzare, achiziție și facturi, coloana **Tip
   comandă** / **Tip Factura** se afișează din meniul coloanelor opționale. În căutarea comenzilor de
   vânzare există filtrul pe **Tip comandă** și gruparea **Tip comandă**. În **Vânzări → Raportare** și
   **Achiziții → Raportare**, dimensiunea **Tip comandă** este disponibilă în pivot și grafic.
2. **Verificați** — suma pe tipuri este egală cu totalul fără grupare; comenzile fără tip apar într-un
   grup separat (*Nedefinit*); niciun tip nu apare la o comandă din alt flux.
3. **Mai departe** — exportați pivotul în Excel cu butonul de descărcare din bara pivotului, dacă e
   nevoie.

### Note de monografie și raportare

Modulul nu generează note contabile proprii. Notele facturilor rămân cele standard ale Odoo; tipul
influențează doar câmpurile completate (de exemplu jurnalul), deci și seria facturii.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale`, `sale_stock` | Tipul pe comanda de vânzare, rutele aplicate liniilor, analiza vânzărilor |
| `purchase` | Tipul pe comanda de achiziție, jurnalul facturii de furnizor, analiza achizițiilor |
| `account` | Tipul pe factură |
| `payment` / `website_sale` | Comenzile confirmate prin plată online sau din magazin nu cer tip |

**Ce e automat:** completarea valorilor implicite la alegerea tipului; rutele pe liniile comenzii;
jurnalul facturii de furnizor din comanda de achiziție; ascunderea câmpului de tip când nu există
tipuri; regula de confirmare.

**Ce rămâne manual:** definirea tipurilor și a valorilor implicite; alegerea tipului pe fiecare
document; verificarea valorilor completate.

## 8. Verificări pentru consultant

- [ ] Fără niciun tip definit, câmpul **Tip comandă** nu apare pe comanda de vânzare.
- [ ] După crearea unui tip, câmpul apare, iar alegerea lui completează valorile implicite.
- [ ] Un agent care nu e în **Utilizatori permiși** nu vede tipul respectiv în lista de pe comanda de
  vânzare.
- [ ] Cu opțiunea **Confirmat fără tip comandă** debifată, un agent fără drept nu poate confirma o
  comandă fără tip; cu tip, o confirmă.
- [ ] O comandă plătită online sau acceptată în portal se confirmă și fără tip.
- [ ] Liniile unei comenzi cu tip care are **Rute** generează aprovizionarea pe acele rute.
- [ ] Factura de furnizor creată din comanda de achiziție are jurnalul din câmpul **Jurnal**.
- [ ] Tipul de factură completează valorile implicite pe factura de client și nu mai poate fi schimbat
  după postare.
- [ ] Analiza vânzărilor se poate grupa după **Tip comandă**.
- [ ] Într-un mediu cu mai multe companii, un tip cu **Companie** setată nu apare în cealaltă companie.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| *You do not have the rights to confirm an order without specifying an Order Type.* | Comanda nu are tip, iar utilizatorul nu are dreptul de confirmare fără tip | Alegeți **Tip comandă** sau acordați dreptul utilizatorului |
| Câmpul **Tip comandă** nu apare pe document | Nu există niciun tip pentru acel model (sau pentru compania curentă) | Creați tipul din meniul de configurare al aplicației |
| Valoarea implicită text nu se aplică, iar la alegerea tipului apare o eroare | Valoarea de tip `Char` nu este scrisă între ghilimele | Scrieți textul ca `'valoare'` în **Valoare câmp** |
| Tipul dorit nu apare în listă pe comanda de vânzare | Utilizatorul nu este în **Utilizatori permiși** | Adăugați utilizatorul pe tip sau goliți lista |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`. Capturile
(formularul **Tip înregistrare** cu valorile implicite, comanda de vânzare cu **Tip comandă**, mesajul
de confirmare, factura cu **Tip Factura**, analiza vânzărilor grupată pe tip) se pot genera ulterior
cu skill-ul `fisa-screenshots`.

## 11. Observații pentru manual

- **Utilizatori permiși** filtrează doar tipurile de comenzi de vânzare; la achiziții și facturi toate
  tipurile sunt propuse tuturor.
- Tipul de factură se alege doar pe facturile și notele de credit de client (formularul facturii de
  furnizor nu afișează grupul în care se află câmpul); coloana **Tip Factura** apare totuși în lista
  facturilor.
- Valorile implicite se aplică la alegerea tipului: dacă utilizatorul schimbă tipul, se aplică noile
  valori peste cele existente.
- Opțiunea **Confirmat fără tip comandă** este bifată la instalare; regula de confirmare devine activă
  doar după debifare.
