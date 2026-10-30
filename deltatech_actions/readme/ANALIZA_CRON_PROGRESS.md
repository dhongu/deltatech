# Analiză 19.0: cron-uri cu `_trigger()` → progresul nativ `_commit_progress`

Data: 2026-10-30. Analiză fără modificări de cod. Pereche cu raportul pentru 18.0:
`deltatech_actions/readme/ANALIZA_CRON_PROGRESS.md` pe ramura 18.0 (dhongu/deltatech#3879).
Codurile A1…F9 de mai jos sunt aceleași ca în raportul 18.0.

**Perimetru:**
- `odoo-addons/deltatech`, `bitshop`, `bitshop_ent`, `l10n-romania`, `terrabit` și `proiecte/`.
- Pentru că în 19.0 există arbori Terrabit noi, am inclus și `bitshop_delivery`,
  `bitshop_marketplace`, `bitshop_vendor`, `deltatech_stock_valuation` și `l10n-hungary`.
  `deltatech_service`, `l10n_ro_ent` și `l10n-moldova` nu au niciun apel de
  `_trigger()` sau de progres.

**Exclus:**
- `odoo/`, `enterprise/` și OCA (`others_addons`, `l10n-romania-oca`, `queue`, copia
  `_folder_l10n_ro_oca` din `proiecte/inedit_venture`).
- Worktree-urile `.claude/` și `wt/`.
- Submodulele-copie `proiecte/ptc/terrabit-ro/*` și `proiecte/dovacom/terrabit-solutions/*`,
  care sunt identice cu `odoo-addons`.
- `proiecte/valshop/odoo-custom-popval` are un capitol separat (§2.4).

---

## 1. Mecanismul nativ în 19.0

Sursa: `odoo/odoo/addons/base/models/ir_cron.py`.

### 1.1 Bucla `_run_job` (~liniile 458–555)

- Constante: `MIN_RUNS_PER_JOB = 10` și `MIN_TIME_PER_JOB = 10` secunde.
- Bucla rulează `while status is None and (loop_count < 10 or time.monotonic() < cron_end_time)`,
  unde `cron_end_time = start + 10 s` și e pus o singură dată în context. Bucla se oprește
  abia după **cel puțin 10 rulări și cel puțin 10 secunde**, la `FULLY_DONE` sau la `FAILED`.
  Nu există maximum: cât timp fiecare rulare avansează, bucla continuă.
- La fiecare iterație se creează un nou `ir.cron.progress` cu `done=0` și `remaining=0`,
  plus commit. Valorile lui `_commit_progress` se raportează deci la **iterația curentă**.
- `_callback` face commit singur după succes. În v18 commit-ul se făcea doar în `_run_job`.

Tabelul de decizie (`match (success, done, remaining)`):

| success | done | remaining | Rezultat |
|---|---|---|---|
| False | > 0 | > 0 | iterația următoare: eroarea e considerată temporară, progresul s-a salvat |
| False | altfel | | `FAILED` |
| True | oricât | 0 | `FULLY_DONE` (iar cu `deactivate=True`, cron-ul se dezactivează) |
| True | **0** | > 0, prima iterație | **`PARTIALLY_DONE`**, cu warning „processed no record” |
| True | **0** | > 0, iterațiile următoare | **`PARTIALLY_DONE`** |
| True | > 0 | > 0 | iterația următoare |

### 1.2 Cazul `done == 0` cu `remaining > 0`: buclă infinită

În v18, acest caz înseamnă `FULLY_DONE`: Odoo oprește bucla. În v19 înseamnă `PARTIALLY_DONE`,
deci `_reschedule_asap`. Acesta **inserează acum un `ir_cron_trigger` la `now`**; în v18
`_reschedule_asap` era un `pass`. Cron-ul revine la următorul poll, iar dacă tot nu poate
avansa, revine iar, la nesfârșit. Situațiile tipice sunt `dry_run`, înregistrările care
nu se pot procesa niciodată și erorile prinse într-un `except` care lasă înregistrarea în
domeniu. **Regula: dacă lotul n-a avansat, raportează `remaining=0`.**

### 1.3 `_commit_progress(processed=0, *, remaining=None, deactivate=False)` (~linia 846)

- `done += processed`: valoarea **se adună**, spre deosebire de `_notify_progress`
  din v18, care **setează** valoarea.
- `remaining=None` înseamnă `remaining = max(remaining_vechi - processed, 0)`. O valoare
  explicită suprascrie.
- Face **commit** de fiecare dată.
- **În afara cron-ului** (fără `ir_cron_progress_id`) **face doar commit** și returnează
  `inf`. Dintr-un buton sau un request HTTP, asta comite tranzacția apelantului. De aceea
  toate modulele noastre verifică întâi `context.get("ir_cron_progress_id")`.
- Verifică `progress.cron_id.id == context['cron_id']`.
- **Valoarea returnată** este `max(cron_end_time - now, 0)`, adică timpul rămas **din felia
  de 10 s** a job-ului, **nu** din limita worker-ului. După primele 10 s returnează 0 la
  fiecare apel. Un cron care se oprește la `0` lucrează deci în felii: prima rulare
  procesează cât încape în 10 s, iar următoarele (până la 10 rulări) câte o unitate,
  după care job-ul eliberează worker-ul (`PARTIALLY_DONE`). Este un mecanism de
  *fairness* între cron-uri, nu o protecție la timeout.
- `_notify_progress` există încă, dar e marcat `@api.deprecated("Since 19.0, use _commit_progress")`.

### 1.4 „Run manually” (`method_direct_trigger`, ~linia 150)

- În 19.0 apelează `_acquire_one_job(include_not_ready=True)` și apoi `_process_job`: **aceeași
  buclă ca în worker**, dar în thread-ul HTTP, cu cursor nou. Contextul are `cron_id` și
  `ir_cron_progress_id`.
- Dacă rămâne de lucru după felie, `_reschedule_asap` pune un trigger și restul continuă în
  fundal. **Ramura de rezervă cu `_trigger()` nu mai e necesară** la rularea manuală.
- Webhook-ul `deltatech_cron_monitor_webhook` (`controllers/webhook_controller.py:54`)
  apelează `method_direct_trigger()`. În v19 răspunsul lui durează cel puțin felia de
  10 s plus 10 rulări, iar restul continuă în fundal.
- Apelurile directe din cod, din teste sau din butoane nu au context de cron: acolo ramura
  de rezervă rămâne utilă dacă vrem continuarea în fundal.

### 1.5 Timeout

Mecanismul e identic cu cel din v18: după `timed_out_counter >= 3` cu `done == 0`, rularea e
marcată `FAILED`, iar după 5 eșecuri pe cel puțin 7 zile cron-ul se dezactivează. Diferența
e că `_commit_progress` face commit, deci orice cron care îl apelează e protejat automat
de la primul lot.

---

## 2. Inventar 19.0

Legendă pentru coloana „față de 18.0”: **=** identic, aceeași recomandare; **≠** diferit;
**NOU** nu există în 18.0; **NATIV** folosește deja `_commit_progress`.

### 2.1 Cron-uri care se repornesc singure cu `_trigger()`

| # | Fișier:linie | Față de 18.0 | Ce face / cum știe că mai e de lucru | Recomandare 19.0 |
|---|---|---|---|---|
| A1 | `odoo-addons/deltatech/deltatech_actions/models/res_partner.py:80` | ≠ (minor) | Merge contacte după email. Intrare nouă `_cron_merge_duplicate_contacts_from_settings` (limita din Settings), `array_agg(id ORDER BY id)` și detașează doar perechea unită. Folosește `LIMIT limit+1` | **DA, prioritar.** `remaining` = `count(*)` pe grupuri. Helper-ul se apelează în metoda de bază, nu în `_from_settings` |
| A2 | `…/res_partner.py:123` | ≠ (minor) | Merge companii după CUI, la fel | **DA, prioritar** |
| B1 | `odoo-addons/terrabit/l10n_ro_vat_change/models/res_company.py:75` | = | Remapare TVA 5/9/19 → 11/21 | DA, cu `deactivate=True`. Prioritate mică |
| C1 | `odoo-addons/deltatech/deltatech_queue_job/models/queue_job.py:279` (`_job_runner`) | = | Runner queue_job, `batch_size` 20 / `max_seconds` 50 | **DA.** În v19 bugetul vine natural: `if not _commit_progress(1, remaining=...): break`. Felia de 10 s înlocuiește `max_seconds` și eliberează worker-ul mai des. `remaining` = `search_count(domain pending)` |
| D1/D2 | `odoo-addons/bitshop_delivery/deltatech_delivery/models/delivery.py:795`, `:798` (și copia `proiecte/diginesis/deltatech_delivery/models/delivery.py:425/428`) | = (s-a mutat în `bitshop_delivery`, iar domeniul exclude acum AWB-urile abandonate) | Status AWB, +5 min la backlog, +30 min la polling | **NU** pentru reluare: pauza protejează API-urile curierilor. Opțional `_commit_progress(len(pickings), remaining=0)` pentru log și protecție la timeout |
| E1 | `odoo-addons/l10n-romania/l10n_ro_efactura_enhancement/models/account_move.py:170` | = | Fetch status SPV, +2 min | **NU.** Observația din 18.0 rămâne valabilă: retrigger-ul continuă cât timp există o factură `invoice_sent` |
| E2 | `…/account_move.py:379` | = | Auto-send SPV, +5 min | **NU.** Opțional, doar log. În v19 nu există riscul de suprascriere, fiindcă `_commit_progress` adună, dar se face și commit în E1 |
| G1 | `odoo-addons/deltatech/deltatech_image_optimize/models/ir_attachment.py:634` (`_dt_bg_remove_cron`) | **NOU** | Elimină fundalul imaginilor din coadă (`bg_removal_state = pending`), câte `batch`, cu commit per imagine; `remaining` = `search_count(pending)` | **DA, ușor.** Commit-ul manual devine `_commit_progress(1, remaining=…)`, fără `_trigger`. Eșecurile trec în `error`, deci lotul avansează. O excepție necontrolată în `_dt_bg_cutout` lasă imaginea `pending`, dar dă `FAILED` (fără `done`), deci nu buclează |
| G2 | `…/ir_attachment.py:662` (`_dt_wm_remove_cron`) | **NOU** | Elimină watermark-ul, același tipar | **DA**, identic cu G1 |
| G3 | `odoo-addons/bitshop_delivery/deltatech_delivery/models/picking_mass_print.py:120` (`_cron_vacuum`) | **NOU** | Șterge PDF-urile de etichete combinate mai vechi decât retenția, câte 1000; requeue la `len == 1000` | **DA.** Sau, mai bine, `@api.autovacuum` care returnează `(done, remaining)`, ca în `deltatech_actions/cleanup_summary.py` |
| G4 | `odoo-addons/bitshop_ent/deltatech_ai_thread_summary/models/ai_thread_summary_mixin.py:431` | **NOU**, hibrid | Rezumate AI; folosește deja `_commit_progress(1)`, dar și `_trigger()` când lotul e plin | **De curățat:** `remaining` = `search_count(pending)`, iar `_trigger()` dispare. De verificat dacă `_ai_summary_update` nu remarchează înregistrarea ca `pending` (prin `write` → `_ai_summary_mark_pending`). Dacă o face, `remaining` nu scade niciodată |
| G5 | `proiecte/ptc/deltatech_ptc/models/deltatech_ptc_import.py:864`, `:887`, `:911` | **NOU** | Import extrase PTC în trei etape (process → bank statements → validate), cu `cr.commit()` manual și retrigger cât timp `search_count(limit=1)` | **DA.** `cr.commit()` devine `_commit_progress(len(batch), remaining=search_count)`. Risc v19: dacă `action_process`/`action_validate` lasă rânduri în aceeași stare fără să pună `error`, ele rămân în domeniu cu `done > 0` până la ultimul lot, apoi cu `done == 0` → buclă. `remaining` trebuie să fie 0 când lotul n-a schimbat starea niciunui rând |
| G6 | `odoo-addons/deltatech_stock_valuation/deltatech_stock_valuation/models/product_valuation.py:1216` (`_auto_refresh_step`) | **NOU** | Mașină cu 7 pași, rulată la fiecare 2 min, un pas pe rulare; la final `cron.active = False` | **Opțional.** `_commit_progress(1, remaining=7 - step)` înlănțuie pașii fără pauza de 2 min, iar `deactivate=True` înlocuiește `active = False`. De decis dacă pauza de 2 min e voită (pași grei) |

### 2.2 Trigger-e de eveniment (rămân așa)

- `deltatech_queue_job/models/queue_job.py:328` (`_cron_trigger`, ETA joburi)
- `bitshop_marketplace/deltatech_marketplace*` (`backend.py:827/1500`, `sale_order.py:334`,
  `stock_picking.py:40`, `stock_move.py:16`, `wizard/sync_product.py:129`,
  `controller/main.py:152`, `binding_product*.py`, `deltatech_marketplace_odoo/purchase_order.py:23/36`),
  plus copiile din `proiecte/diginesis`
- `proiecte/printotecaerp/deltatech_marketplace_brickweb/models/binding_sale_order.py:109/206/585`
- `proiecte/romsystems/terrabit_rsy/models/stock_picking.py:79`
- `deltatech_image_optimize/wizard/image_background_wizard.py:153`, `image_watermark_wizard.py:62`
  (pun imagini în coada pentru G1/G2)
- `bitshop_ent`:
  - `deltatech_ai_knowledge_sync/models/ai_agent.py:47`
  - `deltatech_ai_product_catalog_review/models/ai_product_review.py:183`
  - `deltatech_ai_source_sync/models/ai_source_collection.py:154`
  - `deltatech_ai_source_sync/models/ai_embedding.py:76` (retry cu întârziere pe cron-ul core `ai.ir_cron_generate_embedding`)
  - `deltatech_ai_product_image/models/product_image_search.py:135`
  - `deltatech_ai_website_product/models/ai_agent.py:130`
  - `deltatech_ai_website_product_image/models/ai_agent.py:54`
  - `deltatech_ai_thread_summary/…:156`
- `terrabit_iap_server_ai/controllers/main.py:82`, `terrabit_helpdesk_connector/controllers/main.py:23`
- `deltatech_stock_valuation/models/res_config_settings.py:214/229`, `l10n_hu_zip/hooks.py:17`

### 2.3 Cod care folosește deja progresul nativ (NATIV)

Nicio linie din perimetru nu folosește `_notify_progress`. `_commit_progress` e folosit deja în:

| Fișier:linie | Evaluare |
|---|---|
| `deltatech/deltatech_web_scan/models/web_scan_source.py:173–195` | Corect. Verifică `ir_cron_progress_id`, `remaining` exact, se oprește la timp 0. Model bun |
| `deltatech/deltatech_actions/models/cleanup_summary.py:92` | Corect și documentat: hook-urile `@api.autovacuum` raportează `count` real, ca job-ul de autovacuum să nu fie dezactivat, iar `dry_run` nu cere requeue. Acoperă F3 (PDF-uri) prin autovacuum |
| `bitshop_ent/deltatech_ai_product_catalog_review/models/ai_product_review.py:261–270` | Corect, cu cursor persistent |
| `bitshop_ent/deltatech_ai_source_sync/models/ai_source_collection.py:423–489` | Corect. Adună în `remaining` și colecțiile rămase |
| `bitshop_ent/deltatech_ai_product_image/models/product_image_search.py:154–164` | Corect: `remaining` explicit, apoi `processed=1` |
| `bitshop_ent/deltatech_ai_website_product/models/ai_agent.py:252` | Corect, cu cursor |
| `bitshop_ent/deltatech_ai_knowledge_sync/models/ai_agent.py:62` | Doar `done` (fără `remaining`). Corect pentru protecția la timeout |
| `terrabit/terrabit_iap_server_ai/models/iap_server_ai_request.py:228–243` | Funcțional (`remaining` = lotul curent). **Fără verificarea** `ir_cron_progress_id`: dacă `_cron_process_requests` e apelat vreodată din afara cron-ului, face commit în tranzacția apelantului |
| `bitshop_vendor/deltatech_vendor_products_kramp/models/vendor_feed_sync.py:152` | Corect, protejat de `commit=True`, care e doar pentru cron |
| `l10n-hungary/l10n_hu_zip/models/res_partner.py:130–134` | **Model de referință**: cursor keyset, `remaining` scăzut local, `deactivate=True` la final |
| `proiecte/ptc/deltatech_ptc_auto_awb/models/stock_picking.py:307–319` | Corect, cu `from_cron` explicit |

### 2.4 `proiecte/valshop/odoo-custom-popval` (repo client, `terrabit-ro/valshop`)

Are aproximativ 60 de apeluri `_commit_progress` (delivery, marketplace, meta, GMC, plăți,
GPS etc.) și aproximativ 20 de `_trigger()`, majoritatea de eveniment. Modulele sunt
scrise direct pe API-ul v19, deci nu au nevoie de migrare. Ca observație, pentru un
audit separat: tiparul `_commit_progress(0, remaining=remaining)`, de exemplu la
`popval_spv_purchase_ai_reconciliation/models/agent_reconciliation.py:2487` sau
`popval_delivery_handoff_ops/models/courier_dispatch_batch.py:1078`, trebuie verificat
contra buclei din §1.2. Este sigur doar dacă în aceeași iterație s-a raportat deja
`done > 0` sau dacă `remaining` ajunge la 0 când nu se avansează.

### 2.5 Cron-uri pe loturi fără retrigger (față de 18.0)

| # | Fișier | Față de 18.0 | Recomandare |
|---|---|---|---|
| F1 | `deltatech_actions/models/res_partner.py` (`batch_normalize_company_names`) | ≠: are acum `RETURNING id` + `modified(["name"])` + `check_cleanup_access` | **Bug-ul rămâne:** `offset = 0`, iar regex-ul se potrivește și pe numele normalizate. Se corectează întâi bug-ul, abia apoi se trece pe progres |
| F2 | `deltatech_actions/models/mail_message.py` (`cron_clean_old_messages[_from_settings]`) | ≠: parametrii vin din Settings | DA, cu `remaining=0` la `dry_run` sau dacă `unlink` eșuează. Alternativ, un hook `@api.autovacuum` ca F3 |
| F3 | `deltatech_actions/models/{account_move,sale_order,stock_picking}.py` | ≠: **rezolvat** prin `@api.autovacuum` + `cleanup_summary.autovacuum_run` | Cron-urile proprii `cron_clean_generated_pdfs_from_settings` există încă. De decis dacă mai sunt necesare lângă autovacuum |
| F4 | `deltatech_actions/models/account_move.py` (XML duplicate) | ≠: `max_date_days` și `_from_settings` | NU (motivul e cel din 18.0) |
| F5 | `deltatech_image_optimize/models/ir_attachment.py:475` | = | DA, valoare mare. `_gc_file_store()` rulează doar la `remaining == 0` |
| F6 | `deltatech_invoice_picking_automatically/models/stock_picking.py:39` | = | DA |
| F7 | `deltatech_alternative/models/product.py:135` | ≠: `limit` devine parametru | DA. Numele formate doar din separatori se exclud din `remaining` (obligatoriu în v19) |
| F8 | `proiecte/romsystems/terrabit_product_prices` | = | Opțional (vezi 18.0) |
| F9 | `proiecte/uportho/…/uportho_auto_translate` | = | NU. Cel mult `_commit_progress(n)` pentru protecția la timeout |

---

## 3. Helper-ul `_cron_report_progress` pentru 19.0

Are aceeași semnătură ca în 18.0. Singurul lucru care diferă între versiuni este corpul.

```python
@api.model
def _cron_report_progress(self, cron_xmlid, done, remaining):
    """Raportează lotul curent; returnează timpul rămas (s) din felia cron-ului.

    :param done: elementele procesate în acest lot (nu cumulat)
    :param remaining: elementele rămase după acest lot
    """
    if not done:
        remaining = 0  # nu am avansat: fără asta v19 reia la nesfârșit
    if self.env.context.get("ir_cron_progress_id"):
        # adună `done`, scrie `remaining`, face commit
        return self.env["ir.cron"]._commit_progress(done, remaining=remaining)
    if remaining:
        # apel direct (cod, buton, shell): nu există buclă, continuăm în fundal
        self.env.ref(cron_xmlid)._trigger()
    return float("inf")
```

Varianta pentru 18.0, cu aceeași semnătură și aceeași valoare returnată, ca să portezi
modulele fără modificări:

```python
@api.model
def _cron_report_progress(self, cron_xmlid, done, remaining):
    if not done:
        remaining = 0
    self.env["ir.cron"]._notify_progress(done=done, remaining=remaining)
    if remaining and not self.env.context.get("cron_id"):
        # 18.0: „Run manually” nu reia singur
        self.env.ref(cron_xmlid)._trigger()
    return float("inf")
```

**Regula de portabilitate:** helper-ul se apelează **o singură dată pe callback**, la final,
cu `done` = totalul lotului. În acest caz semantica „setează” din v18 și „adună” din v19
dau același rezultat. Un cron care vrea commit și buget pe element (C1, G1, G2) e cod
specific v19: în buclă apelează `_commit_progress(1, remaining=...)` și se oprește la 0.
În 18.0, același modul păstrează varianta „o dată la final”.

**Unde se pune:**
- Un singur loc comun, de exemplu un `AbstractModel` sau o funcție de modul în
  `deltatech` (similar cu `cleanup_summary.py`), reutilizat de A1, A2, B1, C1, F2, F5–F7, G1–G5.
- Modulele din `bitshop_ent` au deja câte un mic `_commit_progress` local cu aceeași gardă
  `ir_cron_progress_id`. Nu e nevoie să le treci pe helper, doar dacă vrei uniformitate.

---

## 4. Ordinea propusă (19.0)

1. **Helper-ul comun** (§3), cu test pe trei cazuri: cu `ir_cron_progress_id` +
   `cron_id`, fără context (verifici trigger-ul), și cu `done=0` (verifici
   `remaining` forțat la 0). În teste, `_commit_progress` se patch-uiește, ca în
   `deltatech_actions/tests/test_autovacuum_cleanup.py`.
2. **A1 + A2** (`deltatech_actions`): eliminarea `env.ref(...)._trigger()`, plus `savepoint` pe grup.
3. **G1 + G2** (`deltatech_image_optimize`, bg/watermark): schimbare mecanică (commit → `_commit_progress`).
4. **G3** (`bitshop_delivery` mass print vacuum): mutat pe `@api.autovacuum` `(done, remaining)`.
5. **F5** (`deltatech_image_optimize` cron principal) și **F2** (mesaje, eventual prin autovacuum).
6. **G4** (`thread_summary`): `remaining` real, fără `_trigger`, după verificarea re-marcării `pending`.
7. **C1** (`deltatech_queue_job`): în v19 felia de 10 s înlocuiește `max_seconds`. Se testează pe Odoo.sh.
8. **G5** (ptc import), împreună cu clientul, cu garda „lotul n-a schimbat stări → `remaining=0`”.
9. **F6, F7**; **F1** după corectarea bug-ului; **B1** doar dacă modulul mai e folosit.
10. **G6** (stock valuation): decizie de business privind pauza de 2 minute.

Fără schimbare: D1, D2, E1, E2 (pauze intenționate), F4, F8, F9 și trigger-ele de eveniment (§2.2).
Pentru valshop (§2.4) propun un audit separat al tiparului `done=0`/`remaining>0`.
