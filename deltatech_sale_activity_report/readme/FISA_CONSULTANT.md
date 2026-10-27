# Fișă Modul: Jurnalul activității pe comenzile de vânzare

**Modul:** `deltatech_sale_activity_report`
**Utilizator principal:** Manager de vânzări (urmărește cine a lucrat pe ce comandă și când)
**Prioritate:** 🟡 Medie (raport de control al activității echipei; nu atinge contabilitatea)

---

## 1. Scop business

Managerul de vânzări vrea să știe cine a lucrat pe comenzi, în ce zi și ce a schimbat, fără să
deschidă istoricul fiecărei comenzi. Modulul ține un **jurnal zilnic per comandă și per utilizator**:
la prima acțiune a unui utilizator pe o comandă într-o zi se creează o înregistrare de activitate,
iar acțiunile următoare din aceeași zi se adaugă în jurnalul ei. Din jurnal se construiesc liste,
tabele pivot și grafice cu activitatea pe utilizator și pe zi. Înregistrările mai vechi de 2 luni se
șterg automat.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale și nu generează note contabile. Contextul este
operațional: măsurarea volumului de lucru al agenților de vânzări și trasabilitatea modificărilor pe
comenzi (de exemplu la comenzile din magazinul online, procesate de mai mulți operatori).

Jurnalul nu este un registru de audit cu valoare legală: păstrează doar ultimele 2 luni și scurtează
valorile foarte lungi.

## 3. Utilizatori și roluri

| Rol | Ce vede / ce face |
|---|---|
| Vânzări / Utilizator: doar documentele proprii | Generează înregistrări prin lucrul pe comenzi; poate citi doar înregistrările comenzilor proprii sau fără agent |
| Vânzări / Utilizator: toate documentele | Generează înregistrări; poate citi înregistrările tuturor comenzilor |
| Vânzări / Administrator | Vede meniul **Înregistrări activitate** și are drepturi complete pe jurnal |

Jurnalul este scris de sistem, nu de utilizatori: agenții nu pot crea sau modifica înregistrări
manual. Meniul de raportare al aplicației Vânzări este vizibil doar administratorilor de vânzări.
Se jurnalizează doar acțiunile utilizatorilor interni reali; acțiunile automate ale sistemului
(utilizatorul `__system__`, activitățile generate automat) nu apar.

Roluri recomandate pentru testare: doi agenți de vânzări (utilizator intern, „doar documentele
proprii”) și un administrator de vânzări care citește raportul.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile. Pentru demo sunt necesare:

- 2–3 comenzi de vânzare, cu agenți diferiți;
- doi utilizatori interni cu drept de vânzări, care modifică aceste comenzi în aceeași zi.

Fiecare înregistrare de activitate conține: **Comanda de vânzare**, **Data modificării**,
**Utilizator**, **Stare** (starea comenzii: Ofertă, Ofertă trimisă, Comandă de vânzare,
Anulată), **Etapă** (doar dacă este instalat modulul de etape pentru comenzile online), indicatorii
**AWB Generated**, **Chatter Message**, **Tags Changed** și textul jurnalului (**Log**).

## 5. Configurare inițială

1. Instalați modulul `deltatech_sale_activity_report` (depinde de `sale` și `data_recycle`).
2. Atribuiți utilizatorilor drepturile de vânzări dorite (vezi secțiunea 3).
3. Regula de curățare se creează la instalare: în aplicația **Curățare date → Configurare → Reguli →
   Reciclare înregistrări** (*Data Cleaning → Configuration → Rules → Recycle Records*) apare regula
   **Sale Order Activity Record**, automată, care șterge înregistrările cu **Data modificării** mai
   veche de 2 luni. Perioada se poate schimba din regulă.
4. Nu există alte setări: jurnalizarea pornește imediat după instalare.

## 6. Flux de utilizare

### Pasul 1 — Lucrul pe comenzi (generarea jurnalului)

Agentul lucrează obișnuit în **Vânzări → Comenzi → Oferte** sau **Vânzări → Comenzi → Comenzi**.
Fără nicio acțiune suplimentară, se jurnalizează:

- **modificările de câmpuri** salvate pe comandă, sub forma `Updated: <Câmp>: <valoare veche> -> <valoare nouă>`;
  pe liniile comenzii se descrie fiecare operație (`Add New (produs)`, `Update`, `Delete` etc.);
  câmpurile de tip fișier (etichete AWB, semnături) nu se jurnalizează;
- **butoanele** de pe comandă: Confirmă, Anulează, Trecere în ofertă, Blochează, Deblochează,
  Trimite prin e-mail (în jurnal: `Button Clicked: Confirm`, `Cancel`, `Set to Quotation`, `Lock`,
  `Unlock`, `Send by Email`);
- **mesajele** postate în discuția comenzii (`Message: <text>`), cu bifa **Chatter Message**;
- **programarea unei activități** pe comandă (creează înregistrarea zilei, fără text în jurnal);
- schimbarea **etichetelor** (bifa **Tags Changed**) și generarea AWB-ului, când etapa comenzii
  devine „Pre advice” (bifa **AWB Generated**).

Fiecare rând din jurnal începe cu ora (`HH:MM:SS`). O comandă lucrată de doi agenți în aceeași zi are
două înregistrări, câte una pentru fiecare.

### Pasul 2 — Lista înregistrărilor de activitate

Managerul deschide **Vânzări → Raportare → Înregistrări activitate** (*Sales → Reporting → Activity
Records*). Lista se deschide filtrată implicit pe **Luna aceasta** și are coloanele **Comanda de
vânzare**, **Data modificării**, **Stare**, **Etapă**, **Utilizator**.

1. **Găsește pe ecran** — fiecare rând este o pereche comandă–utilizator–zi.
2. **Verifică** — comenzile modificate azi de agenți apar cu data de azi și cu utilizatorul care le-a
   modificat; o comandă modificată de un singur agent de mai multe ori azi apare **o singură dată**;
   coloana **Stare** arată starea comenzii la ultima acțiune.
3. **Treci mai departe** — folosiți filtrele **Azi**, **Ieri**, **Luna aceasta**, **Anul acesta** și
   grupările **Utilizator**, **Etapă**, **Data** pentru analiza dorită.

Din listă nu se pot crea înregistrări noi.

### Pasul 3 — Detaliul unei înregistrări

Clic pe un rând deschide formularul **Activity Record**:

- secțiunea **Basic Information**: comanda, data, starea, etapa, utilizatorul;
- secțiunea **Tracked Events**: bifele **AWB Generated**, **Chatter Message**, **Tags Changed**;
- pagina **Log**: jurnalul zilei, numai în citire, cu toate modificările în ordine cronologică.

Verificați că textul din **Log** corespunde modificărilor făcute de agent în Pasul 1 (valoarea veche
și valoarea nouă pentru fiecare câmp).

### Pasul 4 — Analiza pivot și grafic

Din aceeași acțiune, comutați pe vizualizarea **Pivot**: pe rânduri apar utilizatorii și etapele, pe
coloane zilele. Valoarea din celulă este numărul de comenzi lucrate de utilizator în ziua respectivă.

1. **Găsește pe ecran** — totalul pe rândul unui utilizator = numărul de perechi comandă–zi lucrate.
2. **Verifică** — totalul general este egal cu numărul de rânduri din lista filtrată identic.
3. **Treci mai departe** — tabelul se poate descărca în Excel cu butonul de descărcare al
   vizualizării pivot; vizualizarea **Grafic** arată distribuția pe etape.

### Pasul 5 — Curățarea automată

Regula **Sale Order Activity Record** din **Curățare date** șterge automat înregistrările mai vechi de
2 luni, la rularea programată a mecanismului de reciclare. Raportul acoperă astfel în permanență
doar ultimele două luni.

### Note de monografie și raportare

Nu se generează note contabile (Dr/Cr). Raportul este exclusiv de activitate.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale` | comenzile de vânzare jurnalizate, meniul de raportare |
| `data_recycle` | ștergerea automată a înregistrărilor mai vechi de 2 luni |
| `deltatech_website_sale_status` (opțional) | furnizează **Etapa** comenzii (Plasată, În procesare, Pre advice, În livrare etc.); fără el, coloana **Etapă** rămâne goală |

**Ce e automat:** crearea înregistrării zilnice, adăugarea fiecărei acțiuni în jurnal, bifele de
evenimente, ștergerea după 2 luni.

**Ce rămâne manual:** citirea și interpretarea raportului; ajustarea perioadei de păstrare în regula
de reciclare, dacă e nevoie.

## 8. Verificări pentru consultant

- [ ] Un agent modifică o comandă (ex. clientul sau cantitatea pe o linie): apare o înregistrare cu data
  de azi și numele lui.
- [ ] A doua modificare în aceeași zi, de același agent, nu creează o înregistrare nouă, ci adaugă un
  rând în **Log**.
- [ ] Un al doilea agent care modifică aceeași comandă are propria înregistrare.
- [ ] Confirmarea comenzii apare în **Log** ca `Button Clicked: Confirm`, iar **Stare** devine
  „Comandă de vânzare”.
- [ ] Un mesaj postat în discuție bifează **Chatter Message**.
- [ ] Un agent „doar documentele proprii” nu poate citi înregistrările comenzilor altui agent.
- [ ] Pivotul arată numărul corect de comenzi pe utilizator și zi.
- [ ] Regula **Sale Order Activity Record** există în **Curățare date**, cu 2 luni.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Meniul **Înregistrări activitate** nu apare | Utilizatorul nu este administrator de vânzări (meniul **Raportare** e restricționat) | Atribuiți **Vânzări / Administrator** sau citiți jurnalul prin alt acces |
| Lista e goală | Filtrul implicit **Luna aceasta** și nicio modificare în lună, sau înregistrările au fost șterse după 2 luni | Scoateți filtrul; verificați regula de reciclare |
| Lipsesc modificări făcute de un import sau de o acțiune automată | Se jurnalizează doar utilizatorii interni reali, nu sistemul | Comportament intenționat |
| Valori trunchiate cu `… (+N chars)` | Valoarea depășește plafonul (200 caractere pe câmp, 2000 pe linii/mesaj) | Comportament intenționat, jurnalul rămâne lizibil |
| Coloana **Etapă** goală | Nu este instalat modulul care adaugă etapa comenzii | Normal fără `deltatech_website_sale_status` |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Capturile
pentru pașii 2–4 (lista, formularul, pivotul) se pot genera ulterior cu skill-ul `fisa-screenshots`.

## 11. Observații pentru manual

- De subliniat regula „o înregistrare pe comandă, pe utilizator, pe zi”: pivotul numără comenzi
  lucrate, nu numărul de modificări.
- Textul jurnalului este în engleză (`Updated:`, `Button Clicked:`, `Message:`) și conține etichetele
  câmpurilor în limba utilizatorului.
- Perioada de păstrare de 2 luni trebuie comunicată clientului: raportul nu este o arhivă.
