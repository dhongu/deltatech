# Fișă Modul: Tipuri de documente (comenzi de vânzare, comenzi de achiziție, facturi)

**Modul:** `deltatech_record_type`
**Utilizator principal:** Administrator funcțional, Responsabil vânzări/achiziții, Contabil
**Prioritate:** 🟡 Medie (clasificare și automatizare de introducere; nu generează note contabile proprii)

---

## 1. Scop business

Modulul permite companiei să împartă **comenzile de vânzare, comenzile de achiziție și facturile** pe
**tipuri definite de ea** (de exemplu „Vânzare en-gros", „Vânzare retail", „Achiziție import",
„Factură avans"). Pentru fiecare tip se pot stabili:

- **cine are voie să-l folosească** (lista de utilizatori permiși);
- **valori implicite** care se completează automat pe document la alegerea tipului (depozit, jurnal,
  termen de plată, echipă de vânzări etc.);
- **rutele de stoc** aplicate liniilor comenzii de vânzare (de exemplu livrare directă de la furnizor);
- **obligativitatea tipului** la confirmarea comenzii, pentru utilizatorii fără dreptul de excepție.

Rezultatul: mai puține erori de completare, rapoarte și filtre pe tip și un circuit diferit de
procesare pentru fiecare tip de comandă, fără personalizări separate.

## 2. Bază legală și context

Modulul nu are o bază legală proprie: este un instrument de organizare internă. Tipul documentului
**nu modifică** conținutul fiscal al facturii și nu generează note contabile. Contextul operațional:
companiile care trebuie să trateze diferit canalele de vânzare sau categoriile de achiziții, păstrând
în același timp o singură instanță Odoo.

## 3. Utilizatori și roluri

- **Administrator funcțional** — definește tipurile, valorile implicite, rutele și utilizatorii permiși.
- **Operator vânzări / achiziții / facturare** — alege tipul la crearea documentului.
- **Manager** — filtrează și grupează documentele pe tip; hotărăște cine poate confirma fără tip.

Roluri de test recomandate: un administrator și doi operatori, dintre care unul **nu** este în grupul
„Poate confirma comenzi fără tip comandă", ca să se vadă blocarea la confirmare.

## 4. Conturi și date implicate

Modulul **nu folosește conturi contabile** și nu generează note contabile. Datele implicate:

- tipurile de înregistrări (`record.type`): nume, document vizat, utilizatori permiși, rute, companie;
- valorile implicite ale fiecărui tip (câmp, valoare, tip de valoare);
- câmpurile noi de pe documente: **Tip comandă** (Order Type) pe comanda de vânzare și pe cea de achiziție,
  **Tip Factura** (Invoice Type) pe factură; **Jurnal** pe comanda de achiziție.

Date minime pentru demo: cel puțin un tip pentru fiecare document (vânzare, achiziție, factură), un
client, un furnizor, un produs și doi utilizatori interni.

## 5. Configurare inițială

1. Instalați modulul `deltatech_record_type` (atrage `sale`, `sale_stock` și `purchase`).
2. **Setări → Vânzări → Oferte și Comenzi**, opțiunea **„Confirmat fără tip comandă"**
   (Confirmed without record type):
   - **bifată** = toți utilizatorii interni pot confirma comenzi fără tip;
   - **debifată** = doar membrii grupului „Poate confirma comenzi fără tip comandă" pot confirma fără tip.

   După instalare, grupul de excepție îl au doar administratorul și utilizatorul de sistem, deci
   **imediat ce definiți un tip, toți ceilalți utilizatori trebuie să aleagă tipul** la confirmare.
   Acordați grupul doar celor care au nevoie de excepție.
3. Definiți tipurile necesare (vezi Pasul 1). Un document afișează câmpul de tip **doar dacă există
   cel puțin un tip definit pentru el**.
4. Dacă folosiți rute de stoc pe tip, activați **Setări → Inventar → Trasee în mai mulți pași**
   (grupul „Manage Push and Pull inventory flows") — câmpul **Routes** (rute) apare numai atunci.

## 6. Flux de utilizare

### Pasul 1 — Definirea unui tip de comandă de vânzare

**Vânzări → Configurare → Tipuri comandă** → **Nou**. Completați **Nume** (de exemplu „Vânzare en-gros"),
lăsați **Model** = *Comandă de vânzare* (este completat automat când deschideți lista din acest meniu),
alegeți eventual **Utilizatori permisi** (lăsat gol = tipul este disponibil tuturor; restricția se
aplică **doar pe comanda de vânzare**, nu și pe achiziții sau facturi), **Routes** și **Company**
(gol = toate companiile).

![Formularul tipului de comandă de vânzare; „Utilizatori permisi" gol = tip disponibil tuturor](screenshots/01_tip_vanzare_formular.png)

Pe tab-ul **Valori implicite** adăugați câte o linie pentru fiecare câmp care trebuie precompletat:
alegeți **Câmp** (de exemplu *Customer Reference* sau *Payment Terms*) și **valoarea**. Reguli:

- **text și selecții** se scriu **între apostrofuri**, de exemplu `'Comandă en-gros'`: valoarea este
  evaluată ca expresie, iar text scris fără apostrofuri provoacă eroare la alegerea tipului;
- **bife** se scriu `True` sau `False`;
- **numerele** se scriu fără apostrofuri, de exemplu `5`;
- **câmpuri relaționale** (client, termen de plată, depozit) se aleg din lista **Related**; valoarea
  devine identificatorul înregistrării. La alegerea câmpului, Odoo precompletează prima înregistrare
  găsită — verificați-o și schimbați-o dacă nu e cea dorită.

Tipul valorii (*Id*, *Boolean*, *Char*) se stabilește automat după câmp.

![Valorile implicite ale tipului](screenshots/02_valori_implicite.png)

Tipurile pentru **achiziții** se definesc la **Achiziții → Configurare → Tipuri comandă**, iar cele pentru
**facturi** la **Contabilitate → Configurare → Facturare → Tipuri factură**. Ecranul este același; diferă
doar documentul vizat.

![Lista tipurilor de comandă](screenshots/03_lista_tipuri.png)

### Pasul 2 — Alegerea tipului pe comanda de vânzare

**Vânzări → Comenzi → Oferte → Nou**. În formular apare câmpul **Tip comandă**, înaintea clientului.
Sunt oferite doar tipurile pentru comenzi de vânzare la care utilizatorul curent este permis (sau tipurile
fără restricție de utilizatori). La alegerea tipului, valorile implicite definite se aplică automat pe
comandă. Câmpul devine needitabil după confirmare sau anulare.

![Comandă de vânzare cu tipul ales; termenul de plată implicit este aplicat (referința clientului din valorile implicite se vede în tab-ul „Alte informații")](screenshots/04_comanda_vanzare_tip.png)

Modulul face vizibil pe formularul comenzii de vânzare și câmpul **Jurnal** (jurnalul facturii), în
tab-ul **Alte informații**, grupul **Facturare**.

### Pasul 3 — Confirmarea comenzii și blocarea fără tip

La **Confirmare**, dacă utilizatorul **nu** are grupul „Poate confirma comenzi fără tip comandă", există
tipuri definite pentru vânzări și comanda nu are tip, confirmarea este refuzată cu mesajul *„Nu aveți drepturi
pentru a confirma o comandă fără a specifica un tip de comandă."* (în engleză: *You do not have the rights to
confirm an order without specifying an Order Type.*). Comenzile primite de pe
**website** nu sunt blocate (dacă folosiți magazinul online Odoo). La confirmare, dacă linia comenzii nu
are o rută proprie, aprovizionarea folosește **rutele tipului**; câmpul de rută de pe linie rămâne
gol, efectul se vede pe transferurile generate.

![Mesajul de blocare la confirmarea fără tip](screenshots/05_blocare_confirmare.png)

### Pasul 4 — Tipul pe comanda de achiziție

**Achiziții → Comenzi → Cereri de ofertă → Nou**. Câmpul **Tip comandă** apare înaintea furnizorului,
iar câmpul **Jurnal** în tab-ul **Alte informații**, grupul de facturare, după poziția fiscală. Lista
tipurilor **nu este filtrată** după utilizatorii permiși. **Jurnalul ales se transmite facturii de furnizor** generată
din comandă. Tipul se poate schimba doar cât comanda este **ciornă**: după trimiterea cererii de ofertă nu mai
este editabil. Regula de confirmare este aceeași
ca la vânzări, dar **fără excepția pentru website**.

![Comandă de achiziție cu tip și jurnal](screenshots/06_comanda_achizitie_tip.png)

### Pasul 5 — Tipul pe factură

**Contabilitate → Clienți → Facturi → Nou**: câmpul **Tip Factura** (Invoice Type) apare în tab-ul **Alte informații**, grupul **Factură**, după
**Echipă de vânzări**, și se poate edita doar în starea **ciornă**. Câmpul există doar pe **facturile și
notele de credit de client**, nu și pe facturile de furnizor. La alegerea tipului se aplică valorile
implicite ale acestuia pe factură. Tipul **nu se copiază automat** din comanda de vânzare pe factură:
se alege pe factură, separat.

![Factură cu tipul ales](screenshots/07_factura_tip.png)

### Pasul 6 — Filtrare, grupare și analiză

În lista comenzilor de vânzare, coloana **Tip comandă** este disponibilă opțional (la fel în listele de achiziții și de facturi),
iar în căutare apar câmpul de căutare **Tip comandă** și gruparea **Tip comandă**. Rapoartele de
vânzări și de achiziții expun tipul ca dimensiune: se poate grupa după el prin **Grupare personalizată**.

![Comenzi de vânzare grupate pe tip](screenshots/08_grupare_pe_tip.png)

### Note de monografie și raportare

Modulul **nu generează note contabile proprii**. Notele generate la facturare, livrare sau recepție
rămân cele ale modulelor standard; tipul este doar o etichetă de clasificare și o sursă de valori
implicite. Dacă valorile implicite completează **jurnalul** sau **poziția fiscală**, efectul contabil
vine din acele câmpuri, nu din modul.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale` | Câmpul **Tip comandă**, blocarea la confirmare, filtre și coloane |
| `sale_stock` | Rutele tipului se aplică liniilor comenzii de vânzare |
| `purchase` | Câmpurile **Tip comandă** și **Jurnal** pe comanda de achiziție |
| `account` | Câmpul **Tip Factura** pe factură; jurnalul comenzii de achiziție pe factura de furnizor |

**Ce e automat:** completarea valorilor implicite la alegerea tipului; aplicarea rutelor tipului la aprovizionarea
liniilor de vânzare; transmiterea jurnalului de achiziție la factură; blocarea confirmării fără tip.
**Ce rămâne manual:** definirea tipurilor și a valorilor implicite; alegerea tipului pe fiecare
document; alegerea tipului pe factură (nu se preia din comandă).

Modulul nu are legătură cu declarațiile ANAF.

## 8. Verificări pentru consultant

- [ ] Există cel puțin un tip pentru fiecare document folosit (vânzare, achiziție, factură); altfel
  câmpul nu apare.
- [ ] Pe o comandă nouă, la alegerea tipului se aplică valorile implicite definite.
- [ ] Pe comanda de vânzare, un utilizator din lista **Utilizatori permisi** vede tipul; un utilizator
  neinclus **nu** îl vede (pe achiziții și facturi lista nu filtrează).
- [ ] Un utilizator fără grupul de excepție **nu poate confirma** o comandă fără tip; cu grupul, poate.
- [ ] La confirmare, transferurile generate urmează ruta tipului pentru liniile fără rută proprie.
- [ ] Jurnalul ales pe comanda de achiziție ajunge pe factura de furnizor.
- [ ] Tipul nu se poate modifica după confirmare (vânzare) sau după ce comanda iese din ciornă (achiziție).
- [ ] Tipurile cu **Company** completată nu se văd din altă companie, când aceasta nu e activă în selectorul de companii.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| *Nu aveți drepturi pentru a confirma o comandă fără a specifica un tip de comandă.* (EN: *You do not have the rights to confirm an order without specifying an Order Type.*) | Există tipuri pentru document, comanda nu are tip, iar utilizatorul nu are grupul de excepție | Alegeți tipul pe comandă sau acordați grupul „Poate confirma comenzi fără tip comandă" |
| Utilizatorul nu poate alege niciun tip și nici nu poate confirma | Toate tipurile de vânzare sunt restrânse la alți utilizatori, iar el nu are grupul de excepție | Adăugați-l la **Utilizatori permisi** sau acordați grupul de excepție |
| Câmpul **Tip comandă** / **Tip Factura** nu apare | Nu există niciun tip definit pentru acel document | Creați un tip cu **Model** corespunzător |
| Tipul dorit nu apare în lista comenzii de vânzare | Utilizatorul nu este în **Utilizatori permisi**, sau tipul aparține altei companii | Adăugați utilizatorul sau corectați compania |
| Câmpul **Routes** nu apare pe tip | Grupul „Manage Push and Pull inventory flows" nu este activ | Activați **Trasee în mai mulți pași** în Setări → Inventar |
| Eroare la alegerea tipului, valorile implicite nu se aplică | Valoare de tip text scrisă fără apostrofuri (de exemplu `Comandă en-gros` în loc de `'Comandă en-gros'`) | Scrieți textul între apostrofuri; pentru câmpuri relaționale folosiți lista **Related** |

## 10. Capturi de ecran

Capturile sunt **generate automat**, în limba română, din `tests/test_screenshots.py` (mixinul
`ScreenshotCase` din `l10n_ro_doc_screenshots`, import defensiv; testul se sare dacă acesta lipsește),
pe o companie românească în RON. Fișierele din `readme/screenshots/`:

| Fișier | Descriere |
|---|---|
| `01_tip_vanzare_formular.png` | Formularul tipului de comandă de vânzare (nume, utilizatori permiși, rute) |
| `02_valori_implicite.png` | Tab-ul „Valori implicite" cu două linii completate |
| `03_lista_tipuri.png` | Lista tipurilor de comandă de vânzare |
| `04_comanda_vanzare_tip.png` | Comandă de vânzare cu tipul ales și valorile aplicate |
| `05_blocare_confirmare.png` | Mesajul de blocare la confirmarea fără tip, văzut de un utilizator fără drept de excepție |
| `06_comanda_achizitie_tip.png` | Comandă de achiziție cu tip și jurnal (tab „Alte informații") |
| `07_factura_tip.png` | Factură de client cu tipul ales (tab „Alte informații") |
| `08_grupare_pe_tip.png` | Comenzi de vânzare grupate după tipul comenzii |

Comandă de regenerare (din rădăcina monorepo-ului):

```bash
./odoo/odoo-bin -c odoo.conf -d test19 -u deltatech_record_type,l10n_ro_doc_screenshots --test-tags=fise_screenshots --stop-after-init
```

## 11. Observații pentru manual

- Precizați clar că tipul este **clasificare + valori implicite + rute**, fără efect contabil direct.
- Precizați că valorile implicite se aplică **la alegerea tipului** (onchange), deci nu modifică
  documentele existente.
- Explicați regula de acces: fără grupul de excepție, tipul este **obligatoriu** la confirmare, dacă
  există tipuri definite pentru documentul respectiv.
- Meniurile de configurare sunt restrânse la managerii aplicațiilor, dar drepturile de acces ale
  modelului dau citire, scriere, creare și ștergere oricărui utilizator intern: nu prezentați
  definirea tipurilor ca pe o operațiune sigură pentru oricine.
