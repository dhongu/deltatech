# Fișă Modul: Pornirea acțiunilor programate printr-un webhook extern

**Modul:** `deltatech_cron_monitor_webhook`
**Utilizator principal:** Administrator Odoo / consultant tehnic
**Prioritate:** 🟢 Scăzută (modul tehnic; deschide însă o adresă publică, protejată de un token)

---

## 1. Scop business

Acțiunile programate din Odoo (sincronizări, importuri, trimiteri de rapoarte) rulează după
planificatorul intern. Uneori firma vrea să le pornească și să le urmărească dintr-un serviciu extern
de planificare și monitorizare (de exemplu **cron-job.org**, **healthchecks.io**, **EasyCron**): la
ore fixe, independent de planificatorul Odoo, cu alertă când rularea eșuează. Modulul dă fiecărei
acțiuni programate o **adresă webhook** proprie; serviciul extern apelează adresa, Odoo rulează imediat
acțiunea și răspunde cu rezultatul (reușit sau eroare, durata). Accesul se face cu un **token global**,
unul singur pentru toate webhook-urile.

## 2. Bază legală și context

Nu există temei contabil sau fiscal. Contextul este operațional și de securitate: adresa webhook este
publică, deci tokenul trebuie păstrat confidențial și schimbat dacă a fost expus.

## 3. Utilizatori și roluri

| Rol | Ce face |
|---|---|
| Administrator (Setări) | Generează tokenul global, activează webhook-ul pe acțiunile programate |
| Consultant tehnic | Configurează serviciul extern (adresă, metodă, program, autentificare) |
| Serviciul extern | Apelează adresa webhook și urmărește răspunsul |

Roluri recomandate pentru testare: un administrator cu **mod dezvoltator** activ (meniul **Tehnic** este
necesar pentru acțiunile programate).

## 4. Conturi și date implicate

Modulul nu folosește conturi contabile.

Date minime pentru demo:

- o acțiune programată inofensivă (de exemplu una care doar trimite o notificare sau actualizează un
  curs valutar de test);
- adresa publică a bazei (**web.base.url**) accesibilă din internet, dacă se testează cu un serviciu
  extern; local se poate testa din browser.

## 5. Configurare inițială

1. **Setări → Monitor Cron** (aplicația **Cron Monitor** din setări), blocul **Setări de monitorizare
   Cron**, setarea **Securitate webhook**.
2. Apăsați **Generare token** (sau introduceți un token propriu în **Token global webhook**), apoi
   **Salvați**. Dacă după generare câmpul rămâne gol, introduceți manual un token lung și aleator și
   salvați.
3. Sub setare este o mini-instrucțiune pentru **cron-job.org** (adresă, metodă, program, variante de
   autentificare).

## 6. Flux de utilizare

> Fișă text: pașii nu au capturi de ecran.

### Pasul 1 — Activarea webhook-ului pe o acțiune programată

**Setări → Tehnic → Automatizare → Acțiuni programate** → deschideți acțiunea. În tabul **Configurare
Webhook**:

- bifați **Activează webhook-ul**;
- completați **Cod webhook**, un cod unic, de exemplu `sync_partners`;
- copiați **Webhook URL**, calculat automat: `<adresa bazei>/cron/webhook/<cod>?token=<token global>`.

Salvați.

### Pasul 2 — Configurarea serviciului extern

În serviciul extern (de exemplu cron-job.org) creați o sarcină nouă:

- **URL:** adresa copiată la pasul 1;
- **Metodă:** `GET` sau `POST`;
- **Program:** intervalul dorit;
- **Autentificare**, una dintre variante: tokenul în adresă (`?token=...`), antetul HTTP
  `X-Access-Token: <token>`, sau (doar la `POST`) un corp JSON `{"token": "<token>"}` cu
  `Content-Type: application/json`.

### Pasul 3 — Rularea și citirea răspunsului

Porniți sarcina din serviciul extern (sau deschideți adresa în browser). Odoo rulează imediat acțiunea
programată și răspunde în JSON:

1. **Găsiți pe ecran:** codul HTTP și câmpurile răspunsului: `status`, `job_name`, `execution_time`,
   `timestamp` la reușită; `status` și `message` la eroare.
2. **Verificați:** `status` = `success` și cod HTTP 200; `job_name` este acțiunea așteptată; efectul
   acțiunii se vede în Odoo (de exemplu datele sincronizate).
3. **Treceți mai departe:** abia apoi activați programul periodic și alertele din serviciul extern.

Codurile de eroare: **401** — token lipsă sau greșit; **404** — cod webhook inexistent sau webhook
dezactivat; **500** — acțiunea programată a dat eroare (mesajul erorii este în `message` și în jurnalul
serverului).

### Pasul 4 — Starea unei acțiuni

Adresa `/cron/webhook/<cod>/status` (metoda `GET`) întoarce `job_name`, `next_run` (următoarea rulare
planificată) și `active` (dacă acțiunea este activă). Adresa `/cron/healthcheck` răspunde `OK` cât timp
serverul Odoo funcționează și poate fi folosită pentru monitorizarea disponibilității.

### Note de monografie și raportare

Modulul nu generează note contabile (Dr/Cr). Notele generate de acțiunea programată pornită prin
webhook sunt cele ale acțiunii respective.

## 7. Legături cu alte module / declarații

| Modul | Rol |
|---|---|
| `base` | Acțiunile programate, parametrii de sistem (tokenul global) |
| `web`, `mail` | Interfața setărilor și notificarea la generarea tokenului |
| Servicii externe (cron-job.org, healthchecks.io, EasyCron) | Apelează webhook-ul și urmăresc rezultatul |

**Ce e automat:** calculul adresei webhook, verificarea tokenului, rularea imediată a acțiunii,
răspunsul JSON cu rezultatul.

**Ce rămâne manual:** generarea și păstrarea tokenului, activarea webhook-ului pe fiecare acțiune,
configurarea serviciului extern.

## 8. Verificări pentru consultant

- [ ] Tabul **Configurare Webhook** apare în formularul acțiunii programate.
- [ ] **Cod webhook** și **Webhook URL** apar doar după bifarea **Activează webhook-ul**.
- [ ] **Webhook URL** conține tokenul global după salvarea lui în setări.
- [ ] Apelul cu tokenul corect rulează acțiunea și întoarce `success` (HTTP 200).
- [ ] Apelul fără token sau cu token greșit întoarce HTTP 401 și nu rulează acțiunea.
- [ ] Apelul unui cod inexistent sau al unui webhook dezactivat întoarce HTTP 404.
- [ ] Tokenul trimis în antetul `X-Access-Token` sau în corpul JSON este acceptat.
- [ ] Două acțiuni nu pot avea același **Cod webhook**.

## 9. Mesaje de eroare frecvente

| Mesaj | Cauză | Remediere |
|---|---|---|
| `Invalid token` (HTTP 401) | Token lipsă, greșit sau tokenul global nu e setat | Verificați **Token global webhook** și varianta de autentificare din serviciul extern |
| `Invalid webhook code or disabled` (HTTP 404) | Codul nu există sau **Activează webhook-ul** e debifat | Verificați codul și bifa pe acțiunea programată |
| Mesajul erorii Python (HTTP 500) | Acțiunea programată a eșuat | Citiți `message` și jurnalul serverului; corectați acțiunea |
| `Codul webhook trebuie să fie unic!` | Același cod pe două acțiuni | Alegeți alt cod |

## 10. Capturi de ecran

Fișa este **doar text**: modulul nu are capturi ale fluxului și nici test `tests/test_screenshots.py`.
În `static/description/` sunt doar iconița, bannerul și imaginea principală pentru Odoo Apps. Dacă se
vor adăuga capturi, ele se generează cu skill-ul `fisa-screenshots` și se leagă în pașii 1–4 din
secțiunea 6; răspunsurile JSON rămân extrase de text.

## 11. Observații pentru manual

- **Webhook URL** conține tokenul global în clar; oricine are adresa poate porni acțiunea. Adresa se
  păstrează doar în serviciul extern, iar tokenul se schimbă dacă adresa a fost expusă (schimbarea lui
  invalidează toate webhook-urile până la actualizarea serviciului extern).
- Adresa de stare (`/status`) nu cere token: arată numele acțiunii, următoarea rulare și dacă este
  activă oricui cunoaște codul. Alegeți coduri greu de ghicit.
- Acțiunea pornită prin webhook rulează în cererea HTTP; acțiunile lungi pot depăși timpul limită al
  serverului sau al serviciului extern.
- Modulul nu ține un istoric propriu al rulărilor și nu trimite alerte: monitorizarea și alertele vin din
  serviciul extern.
