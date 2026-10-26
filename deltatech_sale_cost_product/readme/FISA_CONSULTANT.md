# Fișă Modul: Costul mărfurilor pe comanda de vânzare

**Modul:** `deltatech_sale_cost_product`
**Utilizator principal:** Manager vânzări, Controller financiar
**Prioritate:** 🟡 Medie (informație de profitabilitate pentru management, fără impact contabil)

---

## 1. Scop business

Managerii de vânzări și controllerii vor să vadă cât au costat mărfurile dintr-o comandă confirmată,
ca să compare costul cu valoarea vândută. Modulul calculează **Costul mărfurilor** al
comenzii în momentul confirmării, îl păstrează pe comandă și îl afișează ca coloană în listele de
comenzi și cotații, cu total pe grup. Valoarea este vizibilă doar utilizatorilor din grupul
**Poate vedea costul mărfurilor**; ceilalți vânzători nu o văd și nu o pot citi.

Ce primește utilizatorul:

- costul comenzii, calculat din prețul de cost al produselor, convertit în unitatea de măsură a liniei
  și în moneda comenzii;
- coloană opțională în liste, cu total pe grup, vizibilă doar pentru grupul autorizat;
- o acțiune de server, rezervată administratorilor, care calculează costul pentru comenzile deja
  confirmate (de exemplu la prima instalare a modulului);
- duplicarea comenzilor fără eroare de acces: costul **nu se copiază** pe comanda nouă, deci și un
  vânzător din afara grupului poate duplica o comandă.

## 2. Bază legală și context

Modulul nu generează înregistrări contabile și nu are o bază legală proprie: este un instrument de
analiză internă. Costul folosit este prețul de cost curent al produsului (câmpul **Cost** de pe fișa
produsului, indiferent de metoda de evaluare a stocului), așa cum este el configurat în Odoo, deci este un cost de management, nu o evaluare contabilă a stocului. Pentru
evaluarea stocului și notele contabile de descărcare de gestiune se folosesc modulele de stocuri și
contabilitate ale suitei.

## 3. Utilizatori și roluri

| Rol | Acțiune |
|---|---|
| Manager vânzări / Controller | Vede costul comenzilor (grupul **Poate vedea costul mărfurilor**) |
| Vânzător | Creează, confirmă și duplică comenzi; nu vede costul dacă nu face parte din grup |
| Administrator | Rulează acțiunea **Calculează costul mărfurilor** pentru comenzile existente |

Roluri recomandate pentru testare:

- un utilizator cu dreptul de vânzător și cu grupul **Poate vedea costul mărfurilor**;
- un al doilea vânzător, fără grupul de cost: nu trebuie să vadă coloana și trebuie să poată duplica o
  comandă confirmată.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile. Date minime pentru demo:

| Dată | Valoare de exemplu |
|---|---|
| Produs | cu **Cost** completat pe fișa produsului (de exemplu 20 RON) |
| Unitate de măsură | cea a produsului sau o altă unitate din aceeași categorie |
| Client | orice partener |
| Comandă | 2 buc din produsul de mai sus, deci cost așteptat 40 RON |

## 5. Configurare inițială

1. Instalați modulul **Sale Cost on Order** (depinde de `sale` și `product`).
2. Atribuiți grupul **Poate vedea costul mărfurilor** utilizatorilor care trebuie să vadă costul
   (**Setări → Utilizatori și companii → Utilizatori**, pe fișa utilizatorului; dacă grupul nu apare
   în fila cu drepturi de acces, activați modul dezvoltator).
3. Verificați că produsele din demo au **Costul** completat pe fișa produsului.
4. Dacă modulul se instalează într-o bază cu comenzi deja confirmate, un administrator rulează o dată
   acțiunea **Calculează costul mărfurilor** (Pasul 4).

## 6. Flux de utilizare

### Pasul 1 — Crearea comenzii

Acțiune: **Vânzări → Comenzi → Cotații → Nou**. Alegeți clientul și adăugați produsul de test, cu
cantitatea 2. Cât timp comanda este cotație, costul nu este calculat și coloana arată 0.

### Pasul 2 — Confirmarea comenzii

Acțiune: butonul **Confirmă** de pe comandă. În momentul în care comanda trece în starea „Comandă de
vânzare”, modulul calculează costul: pentru fiecare linie cu produs și unitate de măsură, ia costul
produsului, îl convertește în unitatea liniei și în moneda comenzii (citit în compania comenzii) și îl
înmulțește cu cantitatea. Costul comenzii este suma liniilor. Pentru exemplul din secțiunea 4 rezultă
40 RON.

### Pasul 3 — Citirea costului în listă

Acțiune: **Vânzări → Comenzi → Comenzi** (sau **Cotații**), cu un utilizator din grupul **Poate vedea
costul mărfurilor**.

1. **Găsește pe ecran** — în listă, coloana **Costul mărfurilor** (opțională, activă implicit, cu valorile
   scrise îngroșat) arată costul fiecărei comenzi; la subsolul listei apare totalul **Total cost al
   mărfurilor**. Coloana se poate ascunde din selectorul de coloane.
2. **Verifică** — costul comenzii confirmate este egal cu suma (cost produs × cantitate) a liniilor, în
   moneda comenzii; o cotație nu are încă cost (0); un utilizator din afara grupului nu vede coloana.
3. **Treci mai departe** — pentru analiză, grupați sau filtrați lista și folosiți totalul de la
   subsol.

### Pasul 4 — Calcularea costului pentru comenzile deja confirmate (administrator)

Acțiune: în **Vânzări → Comenzi → Comenzi**, selectați comenzi, apoi **Acțiuni** (rotița) **→ Calculează costul
mărfurilor**. Acțiunea este disponibilă doar administratorilor (grupul Setări / Administrare). Ea
recalculează costul **tuturor** comenzilor confirmate, nu doar al celor selectate, cu prețurile de cost
de la momentul rulării. Folosiți-o la instalare sau când vreți să actualizați costurile după o
schimbare de preț de cost.

Observație: costul se calculează la confirmare și nu se actualizează singur dacă prețul de cost al
produsului se schimbă ulterior.

### Pasul 5 — Duplicarea unei comenzi

Acțiune: pe o comandă confirmată, **Acțiuni** (rotița) **→ Duplicare**, cu un vânzător din afara grupului de cost.
Comanda nouă se creează în starea Cotație, iar costul mărfurilor **nu se copiază** (rămâne 0), până la
confirmarea noii comenzi. Astfel un utilizator fără drept asupra câmpului poate duplica comenzi fără
eroare de acces.

### Note de monografie și raportare

Modulul nu generează note contabile (nu există linii Dr/Cr). Costul din comandă este doar informativ
și nu influențează facturile, stocurile sau declarațiile.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale` | Comanda de vânzare; costul se calculează la confirmare |
| `product` | Costul produsului, unitatea de măsură și moneda costului |

**Ce e automat:** calculul costului la confirmarea comenzii; neprelucrarea costului la duplicare.

**Ce rămâne manual:** acordarea grupului **Poate vedea costul mărfurilor**; recalcularea costului după
schimbarea prețurilor de cost (acțiunea de server, doar administrator).

Nu alimentează declarații (D300, D394 etc.).

## 8. Verificări pentru consultant

- [ ] Produsul de test are **Costul** completat și comanda de test conține 2 buc.
- [ ] Cotația (neconfirmată) are costul mărfurilor 0 în listă.
- [ ] După **Confirmă**, comanda arată costul așteptat (de exemplu 40 RON pentru 2 × 20 RON).
- [ ] Dacă linia folosește o altă unitate de măsură decât produsul, costul este convertit corect în
      unitatea liniei.
- [ ] Pe o comandă în altă monedă, costul apare în moneda comenzii.
- [ ] Utilizatorul din grupul **Poate vedea costul mărfurilor** vede coloana și totalul de la subsolul listei.
- [ ] Un vânzător din afara grupului nu vede coloana.
- [ ] Același vânzător din afara grupului poate duplica o comandă confirmată, iar comanda nouă este în
      starea Cotație, cu costul 0.
- [ ] Doar administratorul vede acțiunea **Calculează costul mărfurilor**.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Coloana Costul mărfurilor lipsește din listă | Utilizatorul nu face parte din grupul **Poate vedea costul mărfurilor** sau coloana e ascunsă din selectorul de coloane | Adăugați utilizatorul în grup / reafișați coloana |
| Costul comenzii este 0 | Comanda este încă cotație, produsele nu au cost sau comanda confirmată înainte de instalarea modulului | Confirmați comanda, completați costul produselor sau rulați **Calculează costul mărfurilor** |
| Acțiunea **Calculează costul mărfurilor** nu apare | Utilizatorul nu este administrator | Rulați acțiunea cu un utilizator din grupul de administrare |
| Costul nu s-a schimbat după modificarea prețului de cost | Costul se calculează la confirmare | Rulați **Calculează costul mărfurilor** |

## 10. Capturi de ecran

Fișa nu conține capturi de ecran ale pașilor; modulul are doar imaginea de prezentare
`main_screenshot.png`, din `static/description/`.

## 11. Observații pentru manual

- Explicați că este un cost de management (prețul de cost curent al produsului), nu o evaluare contabilă.
- Subliniați că vizibilitatea costului este controlată de grupul **Poate vedea costul mărfurilor**.
- Păstrați avertismentul că costul se fixează la confirmare și se actualizează doar prin acțiunea de
  administrator.
- Menționați că duplicarea comenzii nu copiază costul (de la versiunea 19.0.0.0.5).
- Textul din `DESCRIPTION.md` și `USAGE.md` menționează un câmp „Purchase Cost” pe linia comenzii și un
  raport de marjă; codul curent expune doar costul pe comandă, în liste. Manualul se aliniază la
  această fișă.
