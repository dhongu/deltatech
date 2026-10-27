# Fișă Modul: Costul mărfurilor pe comanda de vânzare

**Modul:** `deltatech_sale_cost_product`
**Utilizator principal:** Manager de vânzări / controller (analiza profitabilității comenzilor)
**Prioritate:** 🟡 Medie (informație de management; nu generează înregistrări contabile)

---

## 1. Scop business

Managerul de vânzări vrea să vadă, direct în lista de comenzi, cât a costat marfa vândută pe fiecare
comandă, fără să deschidă produsele una câte una. Modulul adaugă pe comanda de vânzare câmpul
**Costul mărfurilor** (*Cost of Goods*), calculat la confirmarea comenzii din costul produselor, și
îl afișează ca o coloană cu total în listele de oferte și de comenzi. Coloana este vizibilă doar
utilizatorilor dintr-un grup dedicat, ca datele de cost să nu ajungă la toți agenții.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale: costul este o informație de analiză, păstrată pe
comandă, și nu înlocuiește costul mărfurilor vândute înregistrat la livrare (cont 607 / 371), care
rămâne în sarcina modulelor de stoc și contabilitate. Contextul este operațional: controlul marjei pe
comandă și identificarea comenzilor vândute sub cost.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Utilizator din grupul **Poate vedea costul mărfurilor** (*Can See Cost Of Goods*) | Vede coloana **Costul mărfurilor** și totalul ei în listele de oferte și comenzi |
| Agent de vânzări fără acest grup | Lucrează normal; nu vede costul |
| Administrator (Setări) | Poate rula acțiunea **Calculează costul mărfurilor** pentru recalcularea în masă |

Roluri recomandate pentru testare: un agent fără grup, un manager cu grupul de cost și un
administrator.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile. Date minime pentru demo:

- 2 produse cu **Cost** completat pe fișa produsului (ex. 60 lei și 25 lei);
- o comandă de vânzare cu aceste produse, eventual într-o unitate de măsură diferită de cea de bază
  sau într-o altă monedă decât moneda costului.

Calculul: pentru fiecare linie, **Cost** al produsului (în compania comenzii), convertit din unitatea
de măsură de bază a produsului în unitatea liniei și din moneda costului în moneda comenzii,
înmulțit cu cantitatea comandată. Suma liniilor este **Costul mărfurilor** al comenzii.

## 5. Configurare inițială

1. Instalați modulul `deltatech_sale_cost_product` (depinde de `sale` și `product`).
2. Activați modul dezvoltator, deschideți **Setări → Utilizatori și companii → Grupuri**, căutați
   grupul **Poate vedea costul mărfurilor** și adăugați utilizatorii care trebuie să vadă costul.
   Grupul nu este atribuit implicit nimănui, nici administratorului.
3. Verificați că produsele vândute au **Cost** completat; un produs fără cost contribuie cu 0.

## 6. Flux de utilizare

### Pasul 1 — Confirmarea comenzii

Agentul creează oferta din **Vânzări → Comenzi → Oferte**, adaugă produsele și apasă **Confirmă**.
La confirmare, modulul calculează **Costul mărfurilor** din costul curent al produselor și îl
salvează pe comandă.

Costul este o fotografie din momentul confirmării: o schimbare ulterioară a costului produsului sau a
liniilor comenzii nu îl actualizează automat (vezi Pasul 3).

### Pasul 2 — Citirea costului în lista de comenzi

Managerul deschide **Vânzări → Comenzi → Comenzi** (sau **Oferte**). Coloana **Costul mărfurilor**
este afișată implicit (se poate ascunde din selectorul de coloane), cu totalul **Total cost al
mărfurilor** la baza listei.

1. **Găsește pe ecran** — pe fiecare rând, coloana **Costul mărfurilor** lângă **Total**.
2. **Verifică** — pentru o comandă de test, valoarea este egală cu Σ (cost produs × cantitate),
   în moneda comenzii; ofertele neconfirmate au cost 0; diferența dintre valoarea fără TVA a
   comenzii și **Costul mărfurilor** arată marja brută aproximativă.
3. **Treci mai departe** — grupați pe agent sau pe client ori filtrați perioada; lista se exportă în
   Excel cu **Acțiuni → Export**, incluzând coloana de cost.

### Pasul 3 — Recalcularea în masă

Administratorul selectează una sau mai multe comenzi în listă și alege **Acțiuni → Calculează costul
mărfurilor** (*Calculate Cost of Goods*). Acțiunea recalculează costul pentru **toate** comenzile
confirmate din baza de date, nu doar pentru cele selectate, cu costul curent al produselor.

Folosiți-o după instalarea modulului (comenzile confirmate anterior au cost 0) sau după o actualizare
a costurilor, știind că suprascrie costul din momentul confirmării.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr). Costul de pe comandă este informativ; descărcarea din
gestiune la livrare (607 = 371) o face fluxul standard de stoc.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale` | comenzile de vânzare și listele în care apare coloana |
| `product` | costul produsului (**Cost**) și moneda costului |
| `sale_margin` (standard, opțional) | marja pe linie calculată de Odoo; independentă de acest modul |

**Ce e automat:** calculul costului la confirmare, conversia de unitate de măsură și monedă, totalul
coloanei.

**Ce rămâne manual:** atribuirea grupului de vizibilitate; recalcularea în masă după schimbarea
costurilor.

## 8. Verificări pentru consultant

- [ ] Un utilizator fără grup nu vede coloana **Costul mărfurilor**.
- [ ] Un utilizator cu grup vede coloana și totalul ei.
- [ ] La confirmarea unei comenzi, costul = Σ (cost produs × cantitate).
- [ ] O linie într-o unitate mai mare (ex. bax de 6) este convertită corect (cost unitar × 6 × cantitate).
- [ ] La o comandă în EUR cu costuri în lei, costul apare convertit în EUR.
- [ ] O ofertă neconfirmată are cost 0.
- [ ] **Calculează costul mărfurilor** actualizează comenzile confirmate după o schimbare de cost.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Coloana nu apare | Utilizatorul nu este în grupul **Poate vedea costul mărfurilor** sau coloana a fost ascunsă | Adăugați utilizatorul în grup; reafișați coloana din selector |
| Cost 0 pe comenzi vechi | Comenzile au fost confirmate înainte de instalare | Rulați **Calculează costul mărfurilor** |
| Costul nu urmează modificarea unei linii după confirmare | Costul se calculează doar la confirmare | Rulați recalcularea în masă |
| Acțiunea **Calculează costul mărfurilor** lipsește din meniul **Acțiuni** | Utilizatorul nu este administrator (Setări) | Rulați acțiunea cu un administrator |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Capturile
pentru lista de comenzi cu coloana de cost și pentru acțiunea de recalculare (pașii 2–3) se pot genera
ulterior cu skill-ul `fisa-screenshots`.

## 11. Observații pentru manual

- `readme/DESCRIPTION.md` și `readme/USAGE.md` descriu un câmp **Purchase Cost** pe liniile comenzii și
  o marjă în subsolul comenzii, care nu există în modul: costul este doar la nivel de comandă, în
  liste. Manualul trebuie să urmeze comportamentul din această fișă.
- De subliniat că acțiunea de recalculare acționează pe toate comenzile confirmate, nu pe selecție.
- Costul este „la data confirmării”; pentru marja reală după livrare se folosesc rapoartele de stoc și
  contabilitate.
