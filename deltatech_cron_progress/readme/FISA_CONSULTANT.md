# Fișă Modul: Acțiuni programate care lucrează pe loturi până termină

**Modul:** `deltatech_cron_progress`
**Utilizator principal:** Administrator Odoo / consultant tehnic
**Prioritate:** 🟢 Scăzută (modul tehnic, fără ecrane proprii; îl vor folosi modulele Terrabit cu acțiuni programate pe loturi,
pe 18.0: `deltatech_actions`)

---

## 1. Scop business

Multe acțiuni programate procesează date pe loturi: unirea partenerilor duplicați, ștergerea
atașamentelor vechi, optimizarea imaginilor, facturarea automată a livrărilor. Un lot are o limită
(de exemplu 100 de înregistrări), ca rularea să nu depășească timpul permis de server.

Din Odoo 19, planificatorul rulează din nou o acțiune cât timp ea raportează că mai are de lucru. Dacă
însă acțiunea raportează înregistrări rămase fără să fi procesat vreuna (de exemplu toate dau eroare),
Odoo o reia imediat, iar și iar. Modulul aduce o regulă comună pentru modulele Terrabit: după fiecare
lot, acțiunea spune câte înregistrări a procesat și câte au rămas, progresul se salvează, iar un lot
care nu a procesat nimic oprește rularea. Regula are aceeași formă pe 18.0, 19.0 și 20.0, deci codul
modulelor care o folosesc nu se schimbă la migrare.

## 2. Bază legală și context

Nu există temei contabil sau fiscal. Contextul este operațional. Mecanismul de progres al acțiunilor
programate există din Odoo 18. Din Odoo 19, planificatorul rulează lotul următor imediat, salvează
progresul după fiecare lot, iar butonul **Rulează manual** se comportă la fel ca planificatorul.
Modulul păstrează aceeași regulă de apel pe toate versiunile; mecanismul de dedesubt diferă între ele.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Administrator (Setări, mod dezvoltator) | Pornește manual acțiunile programate și urmărește rularea |
| Consultant tehnic | Verifică în jurnalul serverului că acțiunea a procesat tot și s-a oprit |
| Dezvoltator | Folosește regula comună în acțiunile programate ale modulelor noi |

Roluri recomandate pentru testare: un administrator cu **mod dezvoltator** activ (meniul **Tehnic** este
necesar pentru acțiunile programate) și acces la jurnalul serverului (pe Odoo.sh: **Logs**).

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile.

Date minime pentru demo:

- o acțiune programată a unui modul care folosește regula comună, cu mai multe înregistrări de procesat
  decât limita unui lot (de exemplu 25 de grupuri de contacte duplicate la o limită de 10), ca rularea
  să aibă mai multe loturi.

> **Pe 20.0, deocamdată, niciun modul nu folosește regula**: trecerea `deltatech_actions` (unirea
> partenerilor duplicați, curățarea atașamentelor) urmează. Până atunci nu există o acțiune programată
> de test, iar modulul se verifică prin testele lui automate (secțiunea 8).

## 5. Configurare inițială

1. Modulul nu are setări. Se instalează ca dependență a modulelor care îl folosesc sau direct, din
   **Aplicații**, după ce scoateți filtrul **Aplicații** din căutare.
2. Activați modul dezvoltator: **Setări** → blocul **Instrumente de dezvoltare** → **Activează modul de
   dezvoltare**.
3. Verificați că acțiunea programată de test este activă: **Setări → Tehnic → Automatizare → Acțiuni
   planificate**.

## 6. Flux de utilizare

> Fișă text: modulul nu are ecrane proprii, deci pașii nu au capturi de ecran. Rezultatul se citește în
> jurnalul serverului.

### Pasul 1 — Pornirea manuală a acțiunii programate

**Setări → Tehnic → Automatizare → Acțiuni planificate** → deschideți acțiunea de test → butonul
**Rulează manual**.

Odoo rulează lotul următor imediat, până nu mai rămâne nimic. Dacă după cel puțin 10 loturi și cel
puțin 120 de secunde tot mai e de lucru, rularea se încheie, iar planificatorul o reia cât mai repede, după
celelalte acțiuni gata de rulare.

Ecranul așteaptă până se termină rularea manuală. Ce nu încape în ea continuă prin planificator, care
trebuie să fie pornit pe server.

### Pasul 2 — Citirea rezultatului în jurnalul serverului

1. **Găsiți în jurnal:** la finalul rulării, un rând de forma
   `Job 'Merge duplicate contacts by email' (12) fully done (#loop 3; done 5; remaining 0; duration 1.20s)`.
   Numele este cel salvat la instalarea acțiunii, de obicei în engleză. `#loop` este numărul de loturi
   rulate, iar `done` și `remaining` sunt valorile ultimului lot.
2. **Verificați:**
   - starea este `fully done` și `remaining 0` când nu mai e nimic de procesat;
   - starea este `partially done` cu `remaining` mai mare ca 0 doar când lucrul nu a încăput în
     rularea curentă; la rularea următoare `remaining` scade;
   - în Odoo, datele sunt procesate (de exemplu nu mai există contacte duplicate cu același email).
3. **Treceți mai departe:** abia după ce rularea manuală se termină corect, lăsați acțiunea pe
   programul ei normal.

### Pasul 3 — Lotul care nu poate procesa nimic

Dacă înregistrările rămase nu pot fi procesate, iar modulul care folosește regula tratează eroarea
fiecărei înregistrări, lotul raportează că nu a procesat nimic. Rularea se oprește cu `fully done` și
`remaining 0`, iar acțiunea revine la programul ei normal, fără să fie reluată imediat.

În acest caz `fully done` **nu** înseamnă că totul s-a procesat: căutați în jurnal rândul cu `done 0`
și erorile înregistrărilor, scrise de modulul care folosește regula. Dacă modulul nu tratează erorile,
rularea apare ca `failed`.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr). Notele generate de acțiunile programate care îl folosesc
sunt cele ale acțiunilor respective.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `base` | Acțiunile programate și mecanismul lor de progres |
| `deltatech_actions` | Pe 18.0 folosește regula la unirea partenerilor duplicați și la curățarea atașamentelor; pe 19.0 și 20.0 trecerea urmează |
| `deltatech_cron_monitor_webhook` | Pornește acțiunile din exterior, ca butonul **Rulează manual**; regula funcționează și acolo |

**Ce e automat:** salvarea progresului după fiecare lot, reluarea imediată cât timp mai e de lucru,
oprirea când nu mai e nimic de procesat sau când lotul nu a procesat nimic.

**Ce rămâne manual:** pornirea manuală pentru test, citirea jurnalului, stabilirea limitei lotului în
acțiunea programată, unde modulul care o folosește o permite.

## 8. Verificări pentru consultant

- [ ] Testele automate ale modulului trec (singura verificare posibilă pe 20.0 până la migrarea
      `deltatech_actions`): verificați că rularea testelor din CI (PR / Odoo.sh) e verde sau cereți-o
      dezvoltatorului (`odoo-bin … --test-tags=/deltatech_cron_progress …`).
- [ ] La **Rulează manual**, cu mai multe înregistrări decât limita unui lot, jurnalul arată `#loop`
      mai mare ca 1, iar la final `fully done` și `remaining 0`.
- [ ] Datele sunt procesate integral după rulare (de exemplu nu mai rămân contacte duplicate).
- [ ] Fără date de procesat, jurnalul arată `fully done` cu `#loop 1`.
- [ ] Când înregistrările rămase nu pot fi procesate, rularea se oprește cu `fully done` și
      `remaining 0`, iar acțiunea nu se reia imediat.
- [ ] După terminare, câmpul **Ora Urmatoarei Executii** al acțiunii arată următoarea rulare din program.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| Pe ecran, la **Rulează manual**: „Sarcina „...” este deja în curs de execuție” | Acțiunea rulează deja (planificator sau altă pornire manuală) | Așteptați terminarea rulării în curs |
| În jurnal: `Job '...' ... partially done (... remaining N ...)` la fiecare rulare, cu N care nu scade | Fiecare lot procesează înregistrări, dar numărul celor rămase nu scade: aceleași înregistrări ajung din nou în lot, intră altele noi la fel de repede sau numărarea celor rămase e greșită | Verificați în jurnal erorile înregistrărilor și modulul care raportează progresul |
| În jurnal: `Job '...' ... failed` (la **Rulează manual**, eroarea apare și pe ecran) | Lotul curent a dat eroare înainte să raporteze progresul; loturile terminate înainte rămân salvate | Citiți eroarea din jurnal. Odoo dezactivează acțiunea după cel puțin 5 eșecuri la rând, întinse pe cel puțin 7 zile, și anunță administratorul |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are ecrane proprii și nici test `tests/test_screenshots.py`.
Rezultatul se citește în jurnalul serverului. În `static/description/` sunt doar iconița, imaginea
principală și pagina de descriere pentru Odoo Apps.

## 11. Observații pentru manual

- După fiecare lot, progresul se salvează în baza de date. Dacă serverul oprește rularea pentru
  depășirea timpului, loturile deja terminate rămân procesate, iar rularea următoare continuă cu restul.
- Un lot foarte lung ține ocupat un proces de acțiuni programate. Între loturi, după 10 loturi și
  120 de secunde, acțiunea lasă loc celorlalte.
- Regula se aplică doar acțiunilor programate ale modulelor care o folosesc; acțiunile standard Odoo
  nu se schimbă.
