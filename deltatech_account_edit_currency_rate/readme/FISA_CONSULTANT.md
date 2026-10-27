# Fișă Modul: Curs valutar propriu pe factură

**Modul:** `deltatech_account_edit_currency_rate`
**Utilizator principal:** Contabil (facturi în valută, clienți și furnizori)
**Prioritate:** 🔴 Ridicată (schimbă valorile în lei ale notei contabile și baza TVA a facturii)

---

## 1. Scop business

Odoo convertește o factură în valută la cursul oficial din ziua facturii. În practică, uneori factura
trebuie înregistrată la alt curs: cursul BCE în loc de cel BNR, cursul băncii prin care se face
decontarea, sau cursul din factura furnizorului. Modulul adaugă pe factură un câmp de **curs propriu**:
când este completat, toate valorile în lei ale facturii (liniile, TVA-ul, totalurile, nota contabilă)
se calculează la acest curs, nu la cursul zilei. Când este golit, factura revine la cursul oficial.

## 2. Bază legală și context

Codul fiscal (Legea 227/2015), **art. 290**, stabilește cursul de schimb folosit pentru baza de
impozitare a TVA în cazul operațiunilor în valută: cursul BNR sau cursul BCE din data exigibilității,
ori cursul băncii prin care se face decontarea, când contractul prevede acest lucru. Textul de ajutor
al câmpului amintește această regulă. Modulul nu verifică ce curs se introduce: răspunderea alegerii
cursului rămâne a contabilului.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Contabil (Facturare / Contabilitate) | Introduce cursul propriu pe factura în ciornă, verifică valorile în lei, confirmă factura |
| Manager contabilitate | Verifică facturile confirmate cu curs propriu, emite notele de credit |

Roluri recomandate pentru testare: un utilizator cu drept de **Facturare** sau **Contabil**. Modulul
nu adaugă grupuri sau drepturi.

## 4. Conturi și date implicate

Conturi RO care primesc valorile în lei calculate la cursul propriu:

- **4111** Clienți, **707** / **704** Venituri, **4427** TVA colectată (factură către client);
- **401** Furnizori, **371** / **6xx** Cheltuieli, **4426** TVA deductibilă (factură de furnizor).

Date minime pentru demo:

- moneda **EUR** activă și un curs oficial pentru ziua facturii (de exemplu 4,97 lei/EUR);
- un client și un furnizor;
- un produs cu TVA 21%.

## 5. Configurare inițială

1. Activați moneda EUR: **Facturare / Contabilitate → Configurare → Monede**.
2. Introduceți sau actualizați automat cursul EUR pentru ziua facturii.
3. Instalați modulul; nu are alte setări.

## 6. Flux de utilizare

> Fișă text: pașii nu au capturi de ecran.

### Pasul 1 — Factura în valută, în ciornă

**Facturare → Clienți → Facturi** → **Nou**. Alegeți clientul, moneda **EUR** și adăugați o linie de
100 EUR cu TVA 21%. Factura se calculează la cursul oficial al zilei (4,97 lei/EUR în exemplu).

### Pasul 2 — Introducerea cursului propriu

Deschideți tabul **Alte informații**. În grupul **Contabilitate**, după **Poziție fiscală**, apare
câmpul **Curs valutar** (*Currency Rate Custom*). Câmpul se vede doar dacă moneda facturii este alta
decât moneda companiei.

Introduceți cursul exprimat ca **lei pentru o unitate de valută**, de exemplu `5,0000` (până la 4
zecimale).

Ce se întâmplă: factura se recalculează la cursul introdus. Valorile în lei ale liniilor, TVA-ul și
totalurile se refac imediat; același calcul se face și când factura este creată sau modificată prin
import ori prin integrare, nu doar din formular.

### Pasul 3 — Verificarea valorilor în lei

În tabul **Elemente jurnal** (**Journal Items**):

1. **Găsiți pe ecran:** coloanele **Debit** și **Credit** în lei și coloana **Valoare în valută**.
2. **Verificați:** pentru 100 EUR la cursul 5,0000, venitul este 500,00 lei, TVA-ul 105,00 lei, iar
   clientul 605,00 lei; raportul lei / valută pe fiecare linie este cursul introdus, nu cursul zilei.
3. **Treceți mai departe:** abia după aceste verificări apăsați **Confirmă**.

### Pasul 4 — Factura confirmată

După **Confirmă**, câmpul **Curs valutar** devine needitabil. Pentru a schimba cursul, factura se
readuce în ciornă (**Resetare la ciornă**), se corectează cursul și se confirmă din nou.

### Pasul 5 — Duplicare și notă de credit

- **Duplicarea** facturii **nu** copiază cursul propriu: factura nouă pornește de la cursul oficial al
  zilei ei.
- **Nota de credit** (**Notă de credit** din factura confirmată) păstrează cursul facturii originale,
  ca stornarea să se facă la aceleași valori în lei.

### Note de monografie și raportare

Factură către client, 100 EUR + TVA 21%, curs propriu 5,0000 lei/EUR:

| Cont | Debit (lei) | Credit (lei) |
|---|---|---|
| 4111 Clienți | 605,00 | |
| 707 Venituri din vânzarea mărfurilor | | 500,00 |
| 4427 TVA colectată | | 105,00 |

Factură de furnizor, aceleași valori:

| Cont | Debit (lei) | Credit (lei) |
|---|---|---|
| 371 Mărfuri (sau 6xx) | 500,00 | |
| 4426 TVA deductibilă | 105,00 | |
| 401 Furnizori | | 605,00 |

Diferențele de curs de la încasare sau plată se calculează față de valorile în lei ale facturii (deci
față de cursul propriu) și se înregistrează standard pe **665** / **765**. Baza și TVA-ul în lei ajung
în jurnalele de TVA și în declarațiile care le preiau (D300, D394, SAF-T) cu valorile de la cursul
propriu.

## 7. Legături cu alte module / declarații

| Modul / declarație | Rol |
|---|---|
| `account` | Factura, conversia valutară, nota contabilă |
| Jurnalele de vânzări / cumpărări, D300, D394, SAF-T | Preiau baza și TVA-ul în lei calculate la cursul propriu |

**Ce e automat:** recalcularea valorilor în lei la schimbarea cursului, blocarea cursului pe factura
confirmată, păstrarea cursului pe nota de credit, revenirea la cursul oficial când câmpul se golește.

**Ce rămâne manual:** alegerea și introducerea cursului corect, conform art. 290 din Codul fiscal.

## 8. Verificări pentru consultant

- [ ] Câmpul **Curs valutar** apare în **Alte informații** doar pe facturile în valută.
- [ ] Cu 100 EUR la cursul 5,0000, nota are 500 / 105 / 605 lei.
- [ ] Golirea câmpului readuce valorile la cursul oficial al zilei.
- [ ] Pe factura confirmată câmpul este needitabil; după **Resetare la ciornă** se poate schimba.
- [ ] Factura duplicată nu are curs propriu.
- [ ] Nota de credit are același curs ca factura originală și stornează exact aceleași valori în lei.
- [ ] O factură creată prin import cu cursul propriu completat are valorile în lei la acel curs.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `You cannot change the custom currency rate of the posted entry ... Reset it to draft first.` | Cursul a fost schimbat pe o factură confirmată (de exemplu prin import sau integrare) | Readuceți factura în ciornă, schimbați cursul, confirmați din nou |
| Câmpul **Curs valutar** nu apare | Factura este în moneda companiei (lei) | Nu e nevoie de curs propriu |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Dacă se
vor adăuga capturi, ele se generează cu skill-ul `fisa-screenshots` și se leagă în pașii 1–5 din
secțiunea 6.

## 11. Observații pentru manual

- Cursul se introduce ca **lei pentru o unitate de valută** (5,0000), nu invers.
- În interfața în română câmpul se numește tot **Curs valutar**, ca și cursul standard al facturii;
  manualul îl indică prin poziția lui (tabul **Alte informații**, grupul **Contabilitate**).
- Trimiterea la art. 290 din Codul fiscal se păstrează: modulul nu validează cursul ales.
