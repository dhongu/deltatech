# Fișă Modul: Coordonate geografice pentru locațiile și traseele flotei

**Modul:** `deltatech_fleet_geo`
**Utilizator principal:** Manager flotă (date de bază: locații și trasee)
**Prioritate:** 🟢 Scăzută (extensie de date pentru `deltatech_fleet`, fără flux propriu)

---

## 1. Scop business

Locațiile și traseele din `deltatech_fleet` au doar nume și distanțe. Modulul le adaugă coordonatele
geografice, ca baza de date a flotei să poată fi legată de hărți sau de date de localizare:

- **Latitudine**, **Longitudine** și **Raza** pe locațiile flotei;
- latitudinea și longitudinea punctului de plecare și ale punctului de sosire pe trasee, preluate
  automat din locații;
- latitudine și longitudine pe înregistrările de locație a vehiculelor (fără câmpuri pe ecran în
  această versiune).

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale. Contextul este operațional: pregătirea datelor de
bază ale flotei pentru afișarea pe hartă sau pentru integrarea cu un sistem de urmărire (GPS).

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Manager Flotă (*Fleet: Administrator*) | Completează coordonatele locațiilor; verifică coordonatele traseelor |

Modulul nu adaugă drepturi proprii: folosește drepturile din `deltatech_fleet`, unde locațiile și
traseele pot fi deschise doar de **Manager Flotă**. Pentru testare: un Manager Flotă.

## 4. Conturi și date implicate

Nu se folosesc conturi contabile. Pentru demo sunt necesare două locații cu coordonate (de exemplu
sediul și un client) și un traseu între ele.

## 5. Configurare inițială

1. Instalați modulul `deltatech_fleet_geo` (instalează și `deltatech_fleet`).
2. Nu există setări: câmpurile noi apar direct în formularele locațiilor și traseelor.

## 6. Flux de utilizare

### Pasul 1 — Coordonatele locației

**Flotă → Flotă → Date de bază → Locații**. Lista locațiilor se editează pe rând și nu arată
coordonatele; ele se completează în formularul locației (**Locația**), unde după câmpul **Type** apar
**Latitudine** și **Longitudine**, cu 6 zecimale (de exemplu `44.426765` și `26.102537`). Câmpul
**Raza** (implicit 1,0) există pe locație, dar nu este afișat în formular.

### Pasul 2 — Coordonatele traseului

**Flotă → Flotă → Date de bază → Trasee**, deschideți un traseu. Sub **From** apar **Latitudine de
la** și **Longitudine de la**, iar sub **To** apar **Latitudine la** și **Longitudine la**. Valorile
sunt preluate din locațiile alese; se modifică din locație, nu din traseu. Traseul invers, creat cu
butonul **(creare)**, are coordonatele inversate automat, pentru că inversează locațiile.

### Pasul 3 — Butonul „Preia locația” de pe vehicul

În formularul vehiculului apare butonul **Preia locația** (*Get location*), înaintea stadiului
vehiculului. În această versiune butonul nu face nimic: metoda este un punct de extensie pentru o
integrare GPS și nu are implementare (issue dhongu/deltatech#3542). Nu îl prezentați utilizatorilor
ca funcționalitate.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr) și nu are rapoarte.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `deltatech_fleet` | Locațiile, traseele, locațiile vehiculelor și formularele extinse |
| Integrare GPS / hartă (proiect) | Ar folosi coordonatele și butonul **Preia locația**; nu este inclusă |

**Ce e automat:** coordonatele traseului, din locațiile de plecare și de sosire.

**Ce rămâne manual:** introducerea coordonatelor fiecărei locații; orice afișare pe hartă sau
preluare de poziție a vehiculelor.

## 8. Verificări pentru consultant

- [ ] Formularul locației are câmpurile **Latitudine** și **Longitudine**, cu 6 zecimale.
- [ ] Un traseu afișează coordonatele locațiilor **From** și **To**.
- [ ] Modificarea coordonatelor unei locații se vede pe toate traseele care o folosesc.
- [ ] Traseul invers are coordonatele de plecare și de sosire inversate.
- [ ] Butonul **Preia locația** de pe vehicul nu modifică nimic (comportament cunoscut, issue
  dhongu/deltatech#3542).

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Coordonatele traseului sunt zero | Locațiile traseului nu au coordonate | Completați coordonatele în formularul locației |
| Eroare de acces la deschiderea locațiilor | Utilizatorul are doar rolul *Fleet: Officer* | Acordați rolul **Manager Flotă** |
| **Preia locația** nu are efect | Butonul nu are implementare (dhongu/deltatech#3542) | Comportament cunoscut; necesită dezvoltare de proiect |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`. Capturile
(formularul locației cu coordonate, formularul traseului) se pot genera ulterior cu skill-ul
`fisa-screenshots`.

## 11. Observații pentru manual

- Coordonatele se scriu în grade zecimale (WGS84), cu punct zecimal, nu în grade-minute-secunde.
- Câmpurile **Raza** (pe locație) și coordonatele locațiilor vehiculelor există în baza de date, dar nu
  au loc pe ecran în această versiune; se completează doar prin import sau integrare.
