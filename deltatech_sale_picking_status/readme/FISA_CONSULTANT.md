# Fișă Modul: Starea livrării pe comenzile de vânzare

**Modul:** `deltatech_sale_picking_status`
**Utilizator principal:** Agent de vânzări / responsabil logistică (urmărirea livrărilor)
**Prioritate:** 🟢 Scăzută (îmbunătățire de vizibilitate; nu atinge contabilitatea)

---

## 1. Scop business

Agentul de vânzări trebuie să știe rapid care comenzi mai au livrări deschise și care sunt închise.
Modulul adaugă pe comanda de vânzare câmpul **Starea livrării** (*Picking Status*), cu două valori:

- **Efectuat** (*Done*) — toate transferurile comenzii sunt finalizate sau anulate;
- **În curs** (*In Progress*) — comanda mai are cel puțin un transfer deschis.

Câmpul apare ca etichetă colorată în lista de oferte, în lista de comenzi și pe formularul comenzii,
are filtre de căutare, iar schimbările lui se înregistrează în discuția comenzii.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale și nu generează note contabile. Contextul este
operațional: urmărirea comenzilor cu livrări rămase deschise, de exemplu înainte de facturare sau la
discuțiile cu clientul.

Câmpul este diferit de **Stare livrare** standard din Odoo (*Delivery Status*: nelivrat, început,
livrat parțial, livrat integral): **Starea livrării** a modulului spune doar dacă mai există
transferuri deschise, fără să distingă livrarea parțială.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Agent de vânzări | Filtrează comenzile după starea livrării, o vede pe comandă și în istoric |
| Responsabil logistică / depozit | Validează sau anulează transferurile; starea comenzii se actualizează automat |
| Manager de vânzări | Urmărește comenzile rămase cu livrări deschise |

Modulul nu adaugă grupuri sau drepturi. Roluri recomandate pentru testare: un agent de vânzări și un
utilizator de depozit care validează livrările.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile. Date minime pentru demo:

- un produs cu stoc urmărit și stoc disponibil (ex. 10 bucăți);
- trei comenzi de vânzare: una ofertă neconfirmată, una confirmată cu livrarea nevalidată, una
  confirmată cu livrarea validată.

Regula de calcul a **Stării livrării**:

| Situația comenzii | Starea livrării | Culoare |
|---|---|---|
| Ofertă / ofertă trimisă | În curs | portocaliu |
| Comandă confirmată fără transferuri (ex. doar servicii) | În curs | portocaliu |
| Comandă confirmată, cel puțin un transfer nefinalizat și neanulat | În curs | portocaliu |
| Comandă confirmată, toate transferurile finalizate sau anulate | Efectuat | albastru |
| Comandă anulată | Efectuat | albastru |

O livrare parțială cu restanță lasă comanda **În curs** până la validarea sau anularea restanței.

## 5. Configurare inițială

1. Instalați modulul `deltatech_sale_picking_status` (depinde de `sale_stock`).
2. Nu sunt setări de făcut: câmpul, coloanele și filtrele sunt active imediat; starea comenzilor
   existente se calculează la instalare.

## 6. Flux de utilizare

### Pasul 1 — Confirmarea comenzii și livrarea

Agentul confirmă comenzile în **Vânzări → Comenzi → Oferte**. Depozitul validează livrările din
**Inventar → Operațiuni → Livrări** (una se validează, una rămâne nevalidată). **Starea livrării**
se recalculează automat la confirmarea, rezervarea, validarea sau anularea transferului.

### Pasul 2 — Starea pe formularul comenzii

Pe formularul comenzii, **Starea livrării** apare după câmpul **Termeni de plată**, ca etichetă.
Verificați că o comandă cu livrarea validată arată **Efectuat**, iar una cu livrarea nevalidată
arată **În curs**.

### Pasul 3 — Lista de comenzi

Agentul deschide **Vânzări → Comenzi → Comenzi** (sau **Oferte**).

1. **Găsește pe ecran** — coloana **Starea livrării**, după coloana **Stare facturare**; coloana se
   poate ascunde din selectorul de coloane.
2. **Verifică** — comenzile cu toate livrările validate au eticheta albastră **Efectuat**; cele cu
   livrări deschise și ofertele au eticheta portocalie **În curs**.
3. **Treci mai departe** — aplicați filtrele din Pasul 4.

### Pasul 4 — Filtre

În bara de căutare, meniul de filtre conține, după filtrul **Comenzile mele**:

- **Efectuat** (*Done*) — comenzile fără transferuri deschise (inclusiv cele anulate);
- **În curs** (*In progress*) — comenzile cu transferuri deschise și ofertele.

Pentru o listă de lucru a livrărilor restante, combinați filtrul **În curs** cu un filtru pe comenzile
confirmate. Lista filtrată se poate exporta cu **Acțiuni → Export**.

### Pasul 5 — Istoricul în discuția comenzii

Deschideți o comandă a cărei livrare tocmai a fost validată. În discuția comenzii apare schimbarea
**Starea livrării: În curs → Efectuat**, cu data și utilizatorul.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr). Descărcarea din gestiune la livrare (607 = 371) o face
fluxul standard de stoc, independent de acest modul.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale_stock` | transferurile de livrare ale comenzii, din care se calculează starea |

**Ce e automat:** calculul și actualizarea stării la fiecare acțiune pe transfer, afișarea în liste și
pe formular, înregistrarea schimbărilor în discuție.

**Ce rămâne manual:** validarea sau anularea transferurilor.

## 8. Verificări pentru consultant

- [ ] O ofertă neconfirmată are starea **În curs**.
- [ ] După confirmare, cu livrarea nevalidată, starea este **În curs**.
- [ ] După validarea completă a livrării, starea devine **Efectuat**.
- [ ] O livrare parțială cu restanță lasă starea **În curs**; anularea restanței o trece în **Efectuat**.
- [ ] O comandă anulată are starea **Efectuat**.
- [ ] Filtrele **Efectuat** și **În curs** separă corect comenzile.
- [ ] Schimbarea stării apare în discuția comenzii.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Comandă de servicii rămasă **În curs** | Comanda confirmată nu are transferuri | Comportament al regulii de calcul; filtrați după tipul produselor sau ignorați aceste comenzi |
| Starea rămâne **În curs** deși marfa a plecat | Livrarea nu a fost validată sau are o restanță deschisă | Validați livrarea; anulați restanța dacă nu se mai livrează |
| Comenzi anulate în filtrul **Efectuat** | Anularea închide starea livrării | Combinați filtrul cu starea comenzii |
| Coloana lipsește | A fost ascunsă din selectorul de coloane | Reafișați **Starea livrării** |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Capturile
pentru formular, lista colorată, filtre și istoricul din discuție (pașii 2–5) se pot genera ulterior
cu skill-ul `fisa-screenshots`.

## 11. Observații pentru manual

- De explicat diferența față de **Stare livrare** standard: câmpul modulului nu arată livrarea
  parțială, doar dacă mai sunt transferuri deschise.
- Comenzile anulate apar ca **Efectuat**, iar ofertele și comenzile de servicii ca **În curs**:
  filtrele se combină cu starea comenzii.
- În 20.0 câmpul este înlocuit de **Stare livrare** standard (cu filtre pentru livrarea parțială);
  la actualizare, filtrele salvate se mută automat.
