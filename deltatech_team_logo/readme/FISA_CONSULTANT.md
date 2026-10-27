# Fișă Modul: Siglă diferită pe rapoarte pentru fiecare echipă de vânzări

**Modul:** `deltatech_team_logo`
**Utilizator principal:** Manager vânzări (configurare); agenți de vânzări, facturare și depozit (tipăresc documentele)
**Prioritate:** 🟡 Medie (necesar companiilor care vând mai multe branduri din aceeași firmă)

---

## 1. Scop business

O singură firmă poate vinde sub mai multe branduri. În Odoo standard toate rapoartele PDF poartă
aceeași siglă, a companiei. Modulul adaugă câmpul **Sigla** pe echipa de vânzări: ofertele, comenzile
de vânzare, facturile și avizele de livrare emise pentru o echipă cu siglă proprie tipăresc acea
siglă în antet; toate celelalte documente păstrează sigla companiei.

## 2. Bază legală și context

Modulul nu schimbă datele de identificare ale emitentului de pe documente: denumirea, CUI-ul și
adresa din antet și din subsol rămân cele ale companiei. Se schimbă doar imaginea siglei. Contextul
este comercial: identitatea vizuală a brandului pe documentele trimise clientului.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Manager vânzări (*Sales: Administrator*) | Încarcă sigla pe fiecare echipă de vânzări |
| Agent de vânzări | Tipărește sau trimite oferte și comenzi; documentul preia echipa lui |
| Facturare | Tipărește facturile; factura preia echipa din comandă sau pe cea aleasă manual |
| Depozit | Tipărește avizul de livrare al unei comenzi de vânzare |

Modulul nu adaugă grupuri de drepturi. Pentru testare: un administrator al aplicației Vânzări și un
agent din fiecare echipă.

## 4. Conturi și date implicate

Nu se folosesc conturi contabile și nu se generează note contabile. Pentru demo sunt necesare:

- două echipe de vânzări (de exemplu „Brand A” cu siglă proprie și „Brand B” fără siglă);
- câte o comandă de vânzare pentru fiecare echipă, cu produs stocabil (pentru aviz) și factură;
- sigla companiei setată în **Setări → Companii**, ca termen de comparație.

## 5. Configurare inițială

1. Instalați modulul `deltatech_team_logo` (depinde de `sale_stock`).
2. Deschideți **Vânzări → Configurare → Echipe de vânzări** (*Sales → Configuration → Sales Teams*)
   și intrați în echipa dorită.
3. În colțul din dreapta-sus al formularului, încărcați imaginea în câmpul **Sigla** (*Logo*).
4. Repetați pentru fiecare echipă care vinde sub brand propriu. Echipele fără siglă tipăresc sigla
   companiei.

## 6. Flux de utilizare

### Pasul 1 — Oferta și comanda de vânzare

Creați o ofertă în **Vânzări → Comenzi → Oferte** și alegeți echipa în câmpul **Echipa de vânzări**
(fila **Alte informații**; implicit, echipa agentului). Tipăriți oferta din meniul **Tipăriți** (*Print*) sau trimiteți-o
pe e-mail: antetul PDF-ului arată sigla echipei. După confirmare, comanda tipărită arată aceeași siglă.

### Pasul 2 — Avizul de livrare

Din butonul **Livrare** al comenzii deschideți transferul și tipăriți avizul (**Tipăriți →
Tipărire Livrare**, *Print → Delivery Slip*). Transferul nu are echipă proprie: preia echipa comenzii de
vânzare din care provine, deci avizul are aceeași siglă ca și comanda. Un transfer fără comandă de
vânzare (de exemplu o mutare internă) tipărește sigla companiei.

### Pasul 3 — Factura

Creați factura din comandă. Factura preia echipa comenzii (câmpul **Echipa de vânzări** din fila
**Alte informații**); la o factură creată manual, echipa se alege acolo. Tipărită sau trimisă,
factura arată sigla echipei.

### Pasul 4 — Verificarea pe un document fără siglă de echipă

Tipăriți un document al unei echipe fără siglă, sau un document fără echipă: antetul arată sigla
companiei, exact ca în Odoo standard.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr): schimbă doar imaginea din antetul rapoartelor PDF.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sales_team` | Echipa de vânzări, pe care se adaugă câmpul **Sigla** |
| `sale_stock` | Legătura transfer → comandă de vânzare, din care avizul preia echipa |
| `account` | Factura are propriul câmp **Echipa de vânzări** |
| `web` | Machetele rapoartelor (Standard, Striped, Boxed, Bold, Folder, Wave, Bubble) |

**Ce e automat:** alegerea siglei la tipărire, după echipa documentului, în toate machetele de
raport; revenirea la sigla companiei când echipa nu are siglă.

**Ce rămâne manual:** încărcarea siglei pe fiecare echipă; alegerea echipei corecte pe ofertă sau pe
factura creată manual.

## 8. Verificări pentru consultant

- [ ] Formularul echipei de vânzări are câmpul **Sigla** în colțul din dreapta-sus.
- [ ] Oferta, comanda, factura și avizul unei echipe cu siglă tipăresc sigla echipei.
- [ ] Documentele unei echipe fără siglă și cele fără echipă tipăresc sigla companiei.
- [ ] Avizul preia sigla echipei comenzii de vânzare, nu a utilizatorului care îl tipărește.
- [ ] Datele firmei din antet și subsol (denumire, CUI, adresă) rămân ale companiei.
- [ ] Sigla echipei apare și după schimbarea machetei documentelor din **Setări → Companii →
  Configurare machetă document** (*Configure Document Layout*).
- [ ] PDF-ul atașat la e-mailul trimis din document are aceeași siglă ca cel tipărit.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Documentul tipărește sigla companiei, deși echipa are siglă | Documentul are altă echipă sau niciuna (fila **Alte informații**) | Setați echipa corectă pe document |
| Avizul tipărește sigla companiei | Transferul nu provine dintr-o comandă de vânzare, sau comanda nu are echipă | Verificați comanda sursă a transferului |
| Factura are altă siglă decât comanda | Echipa a fost schimbată pe factură | Corectați câmpul **Echipa de vânzări** pe factură, cât e în ciornă |
| Un raport personalizat nu ia sigla echipei | Raportul nu folosește antetul standard al companiei sau documentul nu are echipă de vânzări | Folosiți antetul standard (`web.external_layout`) în raport |
| Un raport fără nicio siglă în antet | Raportul apelează direct o machetă (de exemplu `web.external_layout_standard`), fără `web.external_layout`; pe 19.0 sigla se afișează doar prin acesta (pe 20.0 se revine la sigla companiei) | Apelați `web.external_layout` în raport |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița și imaginea principală pentru Odoo Apps) și nici test `tests/test_screenshots.py`. Capturile
(formularul echipei cu **Sigla**, oferta, avizul și factura tipărite cu sigla echipei) se pot genera
ulterior cu skill-ul `fisa-screenshots`.

## 11. Observații pentru manual

- Sigla este singurul element care se schimbă: brandurile care au nevoie de alte date de contact pe
  documente au nevoie de altă soluție (de exemplu companii separate).
- Textele de ajutor ale câmpurilor sunt scrise în română în cod și apar la fel pentru utilizatorii în
  altă limbă.
