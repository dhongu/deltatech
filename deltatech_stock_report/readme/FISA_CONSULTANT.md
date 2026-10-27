# Fișă Modul: Analiza pozițiilor din transferuri

**Modul:** `deltatech_stock_report`
**Utilizator principal:** Responsabil stocuri / controlor de gestiune
**Prioritate:** 🟢 Scăzută (raport de analiză, doar citire)

---

## 1. Scop business

Rapoartele standard de stoc arată fie stocul la un moment dat, fie mișcările una câte una. Modulul
adaugă raportul **Picking Analysis**, care arată pozițiile transferurilor efectuate (produs × transfer),
cu partenerul, entitatea comercială, tipul operației, cantitatea și valoarea, într-un tabel pivot sau o
listă. Răspunde rapid la întrebări ca „cât am primit de la furnizorul X în trimestrul trecut, pe
categorii” sau „ce valoare au livrările către clientul Y”.

## 2. Bază legală și context

Modulul nu generează documente sau note contabile. Este un raport de analiză peste transferurile
efectuate, util în controlul de gestiune și la reconcilierea stocurilor cu contabilitatea. Valorile
provin din evaluarea stocului (`stock_account`) și nu înlocuiesc fișa de magazie sau balanța contabilă.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Responsabil stocuri (**Inventory / Administrator**) | Deschide raportul, filtrează, grupează, exportă |
| Controlor de gestiune / contabil | Folosește raportul pentru analize și reconcilieri (cu dreptul de administrator stocuri) |

Raportul este accesibil doar grupului **Inventory / Administrator** (doar citire). Fiecare utilizator vede
doar transferurile companiilor la care are acces.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile direct; valorile provin din valoarea mișcărilor de stoc.

Date minime pentru demo:

- câteva recepții de la doi furnizori și câteva livrări către doi clienți, **validate** (doar
  transferurile efectuate intră în raport);
- produse din cel puțin două categorii;
- un client persoană de contact la o firmă, ca să se vadă diferența dintre **Partner** și **Commercial
  Entity**.

## 5. Configurare inițială

1. Instalați modulul `deltatech_stock_report` (depinde de `stock_account`).
2. Utilizatorul care deschide raportul trebuie să aibă rolul **Inventory / Administrator**.

## 6. Flux de utilizare

### Pasul 1 — Deschiderea raportului

**Inventory → Reporting → Picking Analysis**. Raportul se deschide în vizualizarea pivot, cu rândurile
grupate pe **Picking Type** și apoi pe **Commercial Entity**, iar ca măsuri **Quantity** și **Amount**.

### Pasul 2 — Filtrarea și gruparea

Din bara de căutare:

- filtre rapide **Incoming**, **Internal**, **Outgoing** (după tipul operației) și filtrul de dată
  (**Date**, data efectuării transferului);
- căutare după **Location**, **Category**, **Product**, **Commercial Entity**, **Partner**, **Picking Type**
  și, în mediile cu mai multe companii, **Company**;
- grupări după **Picking type**, **Partner**, **Commercial Entity**, **Category**, **Product**,
  **Location**, **Location Destination**, **Date** și **Company**.

### Pasul 3 — Citirea și verificarea datelor

Găsiți pe ecran: fiecare rând al pivotului este un tip de operație și, sub el, o entitate comercială;
coloanele **Quantity** și **Amount** dau cantitatea și valoarea pozițiilor efectuate.

Verificați înainte de a folosi cifrele:

- perioada din filtrul **Date** este cea dorită și sunt incluse doar transferurile efectuate;
- **Quantity** are semnul destinației: pozitivă când marfa intră într-o locație internă (recepții,
  transferuri interne), negativă când iese din stocul intern (livrări, consumuri);
- **Amount** este valoarea de evaluare a mișcării, afișată pozitiv în ambele sensuri; pentru produsele
  fără valoare de evaluare se folosește prețul unitar al mișcării;
- totalul pe un furnizor pentru recepții corespunde valorii stocului recepționat de la el în perioadă.

Pentru detalii pe poziții, treceți în vizualizarea listă: fiecare rând are transferul, tipul operației,
entitatea comercială, partenerul, produsul, cantitatea și valoarea, cu totaluri pe **Quantity** și
**Amount**. Coloanele **Date**, **Location**, **Location Destination** și **Category** sunt ascunse implicit
și se afișează din selectorul de coloane.

### Pasul 4 — Exportul

Abia după verificarea datelor pe ecran, exportați: în pivot, butonul de descărcare (**Download xlsx**); în
listă, selectați rândurile și **Actions → Export**.

### Note de monografie și raportare

Nu se generează note contabile (Dr/Cr). Raportul citește doar mișcările de stoc efectuate.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `stock` | transferurile și mișcările de stoc analizate |
| `stock_account` | valoarea mișcărilor (coloana **Amount**) |

**Ce e automat:** agregarea pe transfer și produs, semnul cantității după destinație, valoarea din
evaluarea stocului, restricția pe companie.

**Ce rămâne manual:** alegerea filtrelor și a grupărilor, interpretarea și exportul.

## 8. Verificări pentru consultant

- [ ] Meniul **Inventory → Reporting → Picking Analysis** apare pentru **Inventory / Administrator** și
  lipsește pentru un utilizator simplu.
- [ ] Doar transferurile efectuate apar în raport; un transfer anulat sau în așteptare nu apare.
- [ ] O recepție apare cu **Quantity** pozitivă, o livrare cu **Quantity** negativă; **Amount** este
  pozitiv în ambele cazuri.
- [ ] **Amount** pe o recepție este egal cu valoarea de evaluare a stocului primit.
- [ ] Gruparea pe **Commercial Entity** adună persoanele de contact sub firma lor.
- [ ] Un utilizator restricționat la o companie nu vede transferurile altei companii.
- [ ] Exportul din pivot conține aceleași totaluri ca pe ecran.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Meniul **Picking Analysis** nu apare | Utilizatorul nu are rolul **Inventory / Administrator** | Acordați rolul sau folosiți un utilizator cu acest rol |
| Raport gol | Nu există transferuri efectuate în perioada sau filtrele alese | Verificați filtrul de dată și starea transferurilor |
| Valori diferite față de contabilitate | Raportul arată valoarea mișcărilor de stoc, nu soldurile conturilor | Reconciliați pe perioadă și pe tip de operație; verificați mișcările fără evaluare |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului în `static/description/` (acolo sunt doar
iconița, bannerul, sigla și imaginea principală pentru Odoo Apps) și nici test
`tests/test_screenshots.py`. Dacă se doresc capturi, ele se generează cu skill-ul `fisa-screenshots`
(pivotul implicit, filtrele și grupările, lista de poziții) și se leagă apoi în pașii din secțiunea 6.

## 11. Observații pentru manual

- Semnul cantității (pozitiv la intrare în stoc intern, negativ la ieșire) și valoarea mereu pozitivă
  trebuie explicate, ca să nu fie citite greșit la totaluri pe tipuri de operații amestecate.
- Raportul este pentru administratorii de stoc; utilizatorii operaționali nu îl văd.
