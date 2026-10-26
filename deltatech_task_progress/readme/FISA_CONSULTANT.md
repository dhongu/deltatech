# Fișă Modul: Dialog de progres pentru operațiuni lungi

**Modul:** `deltatech_task_progress`
**Utilizator principal:** Consultant tehnic / dezvoltator Odoo (utilizatorii finali văd doar dialogul)
**Prioritate:** 🟢 Scăzută (modul tehnic, de infrastructură; se instalează ca dependență a altor module)

---

## 1. Scop business

Operațiunile lungi (citirea unui PDF pagină cu pagină, trimiterea unui lot de comenzi către curier)
rulate într-o singură cerere blochează ecranul și se opresc la expirarea timpului. Modulul le rulează
**pas cu pas**, câte un element pe cerere și tranzacție, cu mai multe elemente în paralel, într-un
dialog care arată:

- bara de progres, elementele terminate și o estimare a timpului rămas;
- contorul întors de pași (linii citite, înregistrări create);
- elementele eșuate, cu erorile lor, și un buton pentru reluarea lor;
- un buton de oprire, care așteaptă terminarea elementelor aflate în lucru.

Utilizatorul nu are un meniu al modulului: dialogul apare când apasă un buton al unui alt modul.

## 2. Bază legală și context

Modulul nu are implicații contabile sau fiscale și nu generează note contabile. Contextul este
operațional: evitarea cererilor care depășesc timpul limită și reluarea țintită a elementelor eșuate,
fără ca lucrul deja făcut să fie pierdut sau refăcut.

Este folosit de `deltatech_ai_purchase_pdf` (citirea cu AI, pagină cu pagină, a unei facturi de furnizor
în PDF).

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Operator (utilizatorul modulului consumator) | Apasă butonul care pornește operațiunea, urmărește progresul, oprește sau reia elementele eșuate |
| Dezvoltator / consultant tehnic | Adaugă dialogul în modulul consumator, alege elementele, pașii și etichetele |

Roluri recomandate pentru testare: un utilizator cu dreptul de a folosi butonul modulului consumator;
modulul nu adaugă drepturi sau grupuri proprii.

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile și nu creează date proprii (nu are modele persistente, doar un
model abstract `task.progress.mixin`). Pentru demo este nevoie de un modul consumator, cu un buton care
întoarce `_task_progress_action(...)`.

## 5. Configurare inițială

1. Instalați modulul `deltatech_task_progress` (depinde doar de `web`); se instalează de obicei automat,
   ca dependență a modulului consumator.
2. În modelul consumator, adăugați `task.progress.mixin` în `_inherit`. Pentru o acțiune pe listă (cu
   `model`), dialogul se poate porni și direct din `env["task.progress.mixin"]`, fără moștenire.
3. Din butonul dorit, întoarceți `self._task_progress_action("<metoda_pasului>", items=[...], ...)`.
4. Definiți metoda pasului, publică, apelată o dată pentru fiecare element.

## 6. Flux de utilizare

### Pasul 1 — Pornirea dialogului

Operatorul apasă butonul modulului consumator (de exemplu o acțiune din lista de comenzi sau dintr-un
wizard). Se deschide dialogul cu titlul dat de consumator.

- Cu `auto_start` (implicit), elementele pornesc imediat.
- Fără `auto_start`, dialogul arată mai întâi textul de introducere (`intro`), iar elementele pornesc la
  apăsarea butonului **Pornește** (*Start*, sau textul dat în `labels["start"]`).
- Dacă consumatorul a dat o metodă `init`, dialogul afișează **Se pregătește...** (*Preparing...*) cât timp serverul pregătește
  lucrul (citirea unui fișier, întocmirea unui plan); metoda întoarce elementele, numele lor, totalul și
  un detaliu. Dacă pregătirea eșuează, eroarea apare într-un mesaj roșu, iar rularea nu pornește.

### Pasul 2 — Rularea elementelor

Dialogul apelează metoda pasului pentru fiecare element, câte `parallel` deodată (implicit 3), fiecare în
cererea și tranzacția lui. Pe o înregistrare se apelează `înregistrare.pas(element)`; fără înregistrare
(acțiune pe listă, cu `model` dat), `model.browse(element).pas()`.

Pe ecran, operatorul urmărește:

1. **Starea** (**Rulează...**, **Se finalizează...**, **Neterminat**, **Oprit**, **Gata**; în engleză
   *Running...*, *Finishing...*, *Not finished*, *Stopped*, *Done*) și procentul, cu timpul rămas estimat
   (`~N s rămase` / `~N min rămase`; în engleză `~Ns left` / `~Nmin left`) cât timp rulează;
2. **Contorul**: `făcute / total unități`, eventual detaliul în paranteză și numărul adus de pași
   (`— N linii`);
3. dacă consumatorul a cerut `show_items`, **lista elementelor**, fiecare cu starea lui (în așteptare, în
   lucru, reușit, avertisment, eroare) și mesajul pasului.

Un pas poate întoarce un număr (se adună la contor) sau un dicționar cu `status`, `message`, `count`:

| Status | Efect |
|---|---|
| `success` | element terminat |
| `warning` | element terminat, dar de verificat manual; nu se mai rulează niciodată |
| `error` | ca și un pas care ridică o excepție: se reia cu butonul de reluare |

Bara devine galbenă dacă există elemente eșuate, avertismente sau oprire, verde la o rulare curată.

### Pasul 3 — Oprire sau reluare

- **Oprește după elementele în lucru** (*Stop after the current items*) — nu mai pornește elemente noi;
  cele în lucru se termină, restul rămân în așteptare. După oprire, butonul **Rulează elementele rămase**
  (*Run the remaining items*) rulează doar ce nu e terminat.
- Dacă au eșuat elemente, mesajul „N element(e) nu au reușit. Rulați-le din nou pentru a continua.”
  (în engleză „N item(s) failed. Run them again to continue.”) și lista erorilor (`element: mesaj`)
  apar doar când `show_items` este oprit; cu `show_items`, erorile se văd în lista elementelor. După o
  oprire fără erori apare numai butonul de reluare.
- Cât timp ceva rulează, dialogul nu se poate închide (nici cu Escape, nici cu butonul **Închide**,
  *Close*).

### Pasul 4 — Încheierea

Metoda `finish` a consumatorului se apelează după regula modului:

- `finish_mode="auto"` — se apelează la terminarea ultimului element, doar dacă nu a eșuat niciun element;
  dialogul se închide și se deschide acțiunea întoarsă (o previzualizare, înregistrările create);
- `finish_mode="button"` — apare butonul (`labels["finish"]`, implicit **Finalizează**, *Finish*) după
  terminarea rulării;
  se apelează pe elementele terminate chiar dacă altele au eșuat, iar dialogul rămâne deschis dacă
  acțiunea întoarsă nu este o fereastră de înregistrări.

La închiderea dialogului după o rulare completă, dacă există metoda `close`, se apelează și acțiunea ei
se deschide.

### Note de monografie și raportare

Nu se generează note contabile (Dr/Cr): modulul este strict tehnic.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `web` | dependență: dialogul, acțiunea client `deltatech_task_progress.run` |
| `deltatech_ai_purchase_pdf` | consumator: citirea PDF-ului unei facturi de furnizor, pagină cu pagină |

**Ce e automat:** rularea pe elemente, paralelismul, bara de progres, estimarea timpului, reluarea
elementelor eșuate, apelul metodei `finish`.

**Ce rămâne manual / în sarcina consumatorului:** alegerea elementelor și a metodelor pas/`init`/
`finish`/`close`; scrierea rezultatului fiecărui element pe un rând propriu. Pașii care rulează simultan
nu trebuie să scrie pe aceleași rânduri (nici pe înregistrarea însăși), altfel apar erori de
serializare. Un `parallel` mai mare decât numărul de procese HTTP ale serverului doar pune cererile la
coadă.

## 8. Verificări pentru consultant

- [ ] La apăsarea butonului consumator se deschide dialogul, cu titlul și, unde e cazul, textul de
  introducere.
- [ ] Cu `auto_start`, elementele pornesc singure; fără el, pornesc doar la **Pornește**.
- [ ] Contorul arată `făcute / total` cu unitatea corectă, iar procentul ajunge la 100% la final.
- [ ] Cu `show_items`, fiecare element apare cu starea și mesajul lui.
- [ ] Un element care ridică o eroare apare ca eșuat, cu mesajul; **Rulează elementele rămase** îl reia
  fără să refacă elementele terminate.
- [ ] Un pas care întoarce `warning` rămâne terminat și nu se reia.
- [ ] **Oprește după elementele în lucru** oprește pornirea elementelor noi; cele în lucru se termină.
- [ ] Dialogul nu se închide cât timp rulează ceva.
- [ ] Cu elemente eșuate, `finish` nu se apelează (în modul `auto`).
- [ ] La final se deschide acțiunea întoarsă de `finish`.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `finish_mode must be one of ('auto', 'button')` | `finish_mode` are altă valoare | Folosiți `auto` sau `button` |
| `Without a record, give the model of the items, and no init or close` | Acțiunea e construită pe un set gol fără `model`, sau cu `init`/`close` | Dați `model`, fără `init`/`close`, sau construiți acțiunea pe o înregistrare |
| `N item(s) failed. Run them again to continue.` | Unul sau mai multe elemente au eșuat | Citiți erorile din dialog, remediați cauza, apăsați **Rulează elementele rămase** |
| Mesaj roșu în dialog (eroare la pregătire sau la încheiere) | Metoda `init` sau `finish` a consumatorului a eșuat | Remediați cauza din mesaj; închideți dialogul și reporniți operațiunea |
| Erori de serializare pe elemente | Pași simultani scriu pe același rând | Scrieți rezultatul fiecărui element pe un rând propriu, reduceți `parallel` |

## 10. Capturi de ecran

Modulul nu are încă fișiere de capturi: nu are test `tests/test_screenshots.py`, iar dialogul apare doar
din butonul unui modul consumator, deci nu poate fi captat din modulul însuși. În `static/description/`
sunt doar iconița și imaginea principală, fără capturi ale fluxului din secțiunea 6. Capturile dialogului
(pornire, rulare, erori cu butonul de reluare, încheiere) se pot face din modulul consumator
`deltatech_ai_purchase_pdf`, cu skill-ul `fisa-screenshots`, și apoi se leagă în pașii 1–4 din
secțiunea 6.

## 11. Observații pentru manual

- Redactorul manualului păstrează descrierea celor patru situații ale dialogului: pregătire, rulare,
  eșec cu reluare, încheiere.
- Regula elementului cu rând propriu și limita dată de numărul de procese HTTP sunt avertismente pentru
  consultantul tehnic, nu pentru operator.
- Textele dialogului sunt în engleză și se traduc prin fișierul `i18n/ro.po`; consumatorul poate înlocui
  etichetele cu `labels`.
