# ROADMAP — `deltatech_tc`

**Versiune curentă:** 19.0.1.1.3
**Ultima actualizare:** 2026-09-29

Baza **Terrabit Connect**: registrul de stații, coada de joburi, endpoint-urile
`/tc/*` și jobul `http_request`. Depinde de: `base`, `bus`.
Agentul de pe stație este aplicația Tauri
([terrabit-connect-releases](https://github.com/dhongu/terrabit-connect-releases/releases/latest),
v1.6.20 la data de mai sus).

---

## ✅ Realizat

- Registru de stații (`deltatech.tc.station`): cheie API, companie, ultima conectare,
  versiune, sistem de operare și funcții active raportate la heartbeat
- Coadă de joburi (`deltatech.tc.job`), endpoint-uri `/tc/heartbeat`, `/tc/poll`,
  `/tc/result`, `/tc/config/<id>` și jobul `ping`
- Jobul `http_request` (apel HTTP în rețeaua clientului), cu callback-uri limitate
  la metodele `_tc_*` și lista albă de gazde ținută pe stație (19.0.1.1.0)
- Dependența `bus` declarată (19.0.1.1.1)
- `/tc/poll` dă doar joburile stației care întreabă; `/tc/result` acceptă rezultatul
  doar pentru un job `claimed` (19.0.1.1.2)
- Scrierea `last_seen` rărită la 60 de secunde
- Doar antetul `X-Station-Key`; fallback-ul `X-Agent-Key` al agentului Java scos.
  Documentația descrie agentul Tauri (19.0.1.1.3)

---

## 🔜 Planificat

### 1. Securitatea serverului local din agentul Tauri — blocant
În `terrabit-connect-tauri`, `cors_mw` (`src-tauri/src/lib.rs`) întoarce orice
`Origin` primit, iar nicio rută nu cere token. Orice site deschis pe stație poate
apela `/zebra/print`, `/print` (casa de marcat) și `/api/config`, de unde poate
completa `TERRABIT_HTTP_ALLOW`. Asta anulează lista albă a jobului `http_request`.
Reparația are o sesiune separată, pornită pe 29.09.2026. Nimic nou nu se pune pe
canalul `/tc` până nu e închisă.

### 2. Retragerea agentului Java (`terrabit-anaf-agent`)
Cât timp rulează și agentul Java cu aceeași cheie, poll-ul de joburi din Tauri
rămâne oprit (`TERRABIT_POLL_JOBS`), ca să nu ia amândoi același job. După
retragere, poll-ul din Tauri poate porni implicit. Agentul Java are și un
`TrustManager` care acceptă orice certificat, deci nu verifică certificatul Odoo.

### 3. Coadă robustă
- revendicare atomică (`FOR UPDATE SKIP LOCKED`); acum `search` + `write` pot da
  același job la două poll-uri simultane;
- jobul `claimed` fără rezultat se oferă din nou după un timp, cu prag de încercări
  și apoi `error`; acum rămâne `claimed` pentru totdeauna;
- cron de curățenie: șterge joburile `done` și `error` vechi și expiră `pending`-urile
  rămase neridicate.

### 4. Cheia stației hash-uită
Acum cheia stă în clar (`api_key`) și se caută prin egalitate. De trecut pe
sha256 cu sare și comparație constant-time. Cheia s-ar afișa o singură dată, la
generare, deci descărcarea `station.conf` ar trebui legată de regenerare.

### 5. Latență mai mică la joburile interactive
Pentru etichete, un poll la 30 de secunde e prea rar. Variante: long-polling pe
`/tc/poll` sau interval separat pe stațiile cu funcția „labels”.

### 6. Tipărire prin coadă (`deltatech_print_queue`)
Pe baza analizei `mdtrade_print` (MD Trade, 29.09.2026):
- tipuri de job `print_zpl` și `print_pdf`, adăugate cu `selection_add`;
- în agent: `print_zpl` refolosește `zebra::send`; `print_pdf` e nou (SumatraPDF sau
  tipărire nativă pe Windows, `lp` pe macOS și Linux);
- evidență locală a joburilor deja tipărite, ca o confirmare pierdută să nu scoată
  a doua etichetă.

Depinde de punctele 1–3.

### 7. Utilizatorul află când un job pică
Notificare prin `bus` sau activitate pe documentul-sursă când jobul trece în `error`.

### 8. Referințe Java rămase în modulele dependente (`l10n_ro_ent`)
- `l10n_ro_anaf_agent`: link către release-urile `terrabit-anaf-agent` în
  `readme/FISA_CONSULTANT.md`, „Importă agent.conf” și propriul fallback
  `X-Agent-Key` în `controllers/main.py`;
- `l10n_ro_anaf_messages`: „Java + PKCS#11” în `readme/DESCRIPTION.md` și calea
  `TerrabitAnafAgent.java` în `models/anaf_spv_client.py`. Semnarea cu tokenul
  trece încă printr-un helper Java în Tauri, deci formularea trebuie corectată,
  nu doar ștearsă.

### 9. Port pe 20.0
Fiecare punct de mai sus se duce și pe 20.0.

---

## ❓ Decizii deschise

- Când se retrage agentul Java și cine confirmă stațiile migrate?
- Pentru etichete: long-polling pe server sau interval mai scurt pe stație?
- Cheia hash-uită: acceptăm ca `station.conf` să se poată descărca doar la regenerarea cheii?
- PDF pe Windows: SumatraPDF împachetat cu agentul sau tipărire nativă din shell?
