# Fișă Modul: Anularea vânzării curăță cererile de ofertă la furnizor

**Modul:** `deltatech_sale_purchase`
**Utilizator principal:** Agent de vânzări și achizitor (flux make-to-order / dropshipping)
**Prioritate:** 🟡 Medie (evită achizițiile inutile după anularea unei comenzi de vânzare)

---

## 1. Scop business

Când un produs se aprovizionează la comandă (rutele **Aprovizionare la comandă** / *MTO* sau
**Dropship**), confirmarea vânzării generează automat o cerere de ofertă (RFQ) la furnizor. În Odoo
standard, dacă vânzarea se anulează, linia din cererea de ofertă rămâne, iar achizitorul riscă să
comande marfă pentru care nu mai există client. Modulul **șterge automat liniile de achiziție
generate de vânzarea anulată**, cât timp cererea de ofertă este încă în stadiul de ciornă. Când linia
de achiziție servește și alte vânzări, nu o șterge, ci îi scade doar cantitatea vânzării anulate.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale și nu generează note contabile. Contextul este
operațional: sincronizarea între vânzări și achiziții, evitarea stocurilor nedorite și a
comenzilor la furnizor fără acoperire.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Agent de vânzări | Confirmă și, la nevoie, anulează comanda de vânzare |
| Achizitor | Lucrează cererile de ofertă generate; vede liniile dispărute / reduse după anulare |
| Administrator stoc / achiziții | Configurează rutele produselor și gruparea cererilor de ofertă pe furnizor |

Modulul nu adaugă grupuri. Roluri recomandate pentru testare: un agent de vânzări și un achizitor.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile. Date minime pentru demo:

- un furnizor (ex. „Furnizor Demo”);
- un produs stocabil, cu furnizorul în pagina **Achiziție** și rutele **Cumpără** și **Aprovizionare la
  comandă (MTO)** bifate;
- două comenzi de vânzare pentru acest produs (ex. 5 și 7 bucăți).

Pentru testarea liniilor comune, pe furnizor se setează gruparea cererilor de ofertă **Zilnic**,
**Săptămânal** sau **Întotdeauna** (cu gruparea implicită **La comandă**, fiecare vânzare are
propria cerere de ofertă).

## 5. Configurare inițială

1. Instalați modulul `deltatech_sale_purchase` (depinde de `sale_purchase`, `sale_stock` și
   `purchase_stock`).
2. **Inventar → Configurare → Setări**: activați **Rute multi-pas** (*Multi-Step Routes*) și
   dezarhivați ruta **Aprovizionare la comandă** (MTO), dacă nu este activă.
3. Pe produs, pagina **Inventar**: bifați rutele **Cumpără** și **Aprovizionare la comandă**; în
   pagina **Achiziție**, adăugați furnizorul.
4. Nu există setări proprii ale modulului.

## 6. Flux de utilizare

### Pasul 1 — Vânzarea generează cererea de ofertă

Agentul confirmă comanda de vânzare (5 bucăți) din **Vânzări → Comenzi → Oferte → Confirmă**. Odoo
creează automat o cerere de ofertă la furnizor, cu o linie de 5 bucăți, vizibilă din butonul
inteligent **Achiziție** al comenzii sau din **Achiziții → Comenzi → Cereri de ofertă**.

### Pasul 2 — Anularea vânzării cu cererea de ofertă în ciornă

Agentul anulează comanda de vânzare (**Anulează**). Modulul verifică liniile de achiziție generate:

1. **Găsește pe ecran** — în **Achiziții → Comenzi → Cereri de ofertă**, cererea de ofertă a
   furnizorului.
2. **Verifică** — linia produsului vânzării anulate a dispărut; dacă era singura linie, cererea de
   ofertă rămâne goală, în ciornă, și poate fi anulată de achizitor.
3. **Treci mai departe** — achizitorul anulează sau completează cererea de ofertă, după caz.

### Pasul 3 — Linie comună cu altă vânzare

Cu furnizorul grupat **Zilnic / Săptămânal / Întotdeauna**, două vânzări (5 și 7 bucăți) ajung pe
aceeași linie de achiziție de 12 bucăți. La anularea primei vânzări:

- linia nu se șterge, ci scade la 7 bucăți (cantitatea anulată se convertește în unitatea de măsură
  a liniei de achiziție, dacă diferă);
- a doua vânzare își păstrează aprovizionarea.

### Pasul 4 — Cererea de ofertă deja confirmată

Dacă achizitorul a confirmat deja comanda la furnizor, anularea vânzării **nu** modifică comanda de
achiziție: decizia (anulare la furnizor, păstrare pe stoc) rămâne la achizitor.

### Pasul 5 — Scăderea cantității pe vânzare

Dacă agentul scade cantitatea pe o vânzare confirmată (ex. de la 10 la 4), linia din cererea de
ofertă în ciornă scade și ea. Acest comportament este standard în Odoo 19 și nu ține de modul;
testele modulului îl verifică pentru a semnala o eventuală schimbare.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr): acționează doar pe cererile de ofertă în ciornă, înainte
de orice recepție sau factură de furnizor.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `sale_purchase` | legătura vânzare–achiziție pentru serviciile cumpărate |
| `sale_stock` | mișcările de livrare ale vânzării, anulate la anularea comenzii |
| `purchase_stock` | generarea cererilor de ofertă din rutele MTO / dropship și gruparea pe furnizor |

**Ce e automat:** ștergerea liniilor de achiziție exclusive ale vânzării anulate, reducerea liniilor
comune, păstrarea comenzilor de achiziție confirmate.

**Ce rămâne manual:** anularea cererilor de ofertă rămase goale; tratarea comenzilor de achiziție
deja confirmate.

## 8. Verificări pentru consultant

- [ ] Confirmarea vânzării cu produs MTO creează linia în cererea de ofertă a furnizorului.
- [ ] Anularea vânzării șterge linia din cererea de ofertă în ciornă.
- [ ] Cu gruparea pe furnizor **Întotdeauna**, două vânzări împart o linie; anularea uneia lasă linia
  cu cantitatea celeilalte.
- [ ] O vânzare într-o unitate diferită (ex. duzină) scade corect cantitatea în unitatea liniei de
  achiziție.
- [ ] Dacă cererea de ofertă e confirmată, anularea vânzării nu o modifică.

## 9. Mesaje de eroare frecvente

| Mesaj / simptom | Cauză | Remediere |
|---|---|---|
| Linia de achiziție rămâne după anulare | Comanda de achiziție nu mai este în ciornă (trimisă sau confirmată) | Comportament intenționat: achizitorul decide; modulul acționează doar pe ciorne |
| Nu se creează cerere de ofertă la confirmare | Produsul nu are rutele **Cumpără** + **MTO** sau nu are furnizor | Completați rutele și furnizorul pe produs |
| Cerere de ofertă goală rămasă în ciornă | Singura linie a fost ștearsă | Achizitorul anulează cererea de ofertă |

## 10. Capturi de ecran

Fișa este doar text: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Capturile
pentru cererea de ofertă înainte și după anularea vânzării (pașii 1–3) se pot genera ulterior cu
skill-ul `fisa-screenshots`.

## 11. Observații pentru manual

- De subliniat limita „doar cereri de ofertă în ciornă”: după confirmarea la furnizor, modulul nu mai
  intervine.
- Liniile comune apar doar la furnizorii cu grupare **Zilnic / Săptămânal / Întotdeauna**; cu
  gruparea implicită **La comandă**, fiecare vânzare are propria cerere de ofertă.
- `readme/DESCRIPTION.md` atribuie modulului și ajustarea la scăderea cantității; în Odoo 19 aceasta
  este comportament standard (Pasul 5).
