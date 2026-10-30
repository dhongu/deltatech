# Analiză: cron-uri cu `_trigger()` → progresul nativ `_notify_progress` (Odoo 18)

Data: 2026-10-30. Analiză fără modificări de cod. Perimetru: `odoo-addons/deltatech`,
`bitshop`, `bitshop_ent`, `l10n-romania`, `terrabit` și `proiecte/`. Am exclus `odoo/`,
`enterprise/`, OCA (`others_addons`, `l10n-romania-oca`, `proiecte/diginesis/queue_job`) și
copiile din worktree-urile `.claude/worktrees/`.

---

## 1. Cum funcționează mecanismul nativ în v18

Sursa: `odoo/odoo/addons/base/models/ir_cron.py`.

### 1.1 Constante

| Constantă | Valoare | Rol |
|---|---|---|
| `MAX_BATCH_PER_CRON_JOB` | 10 | de câte ori se reia callback-ul într-o singură preluare a job-ului |
| `CONSECUTIVE_TIMEOUT_FOR_FAILURE` | 3 | după 3 timeout-uri consecutive fără progres, rularea se consideră eșuată |
| `MIN_FAILURE_COUNT_BEFORE_DEACTIVATION` | 5 | împreună cu `MIN_DELTA_BEFORE_DEACTIVATION = 7 zile`, cron-ul se dezactivează |

### 1.2 Bucla `_run_job` (liniile 391–455)

Pentru fiecare dintre cele maximum 10 iterații:

1. `_add_progress(timed_out_counter=...)` creează un `ir.cron.progress` cu `done=0`,
   `remaining=0` și `timed_out_counter = contor + 1`. Face **commit înainte** de callback.
   ID-ul ajunge în context ca `ir_cron_progress_id`.
2. Rulează acțiunea server (`_callback`). Codul nostru apelează
   `self.env["ir.cron"]._notify_progress(done=..., remaining=...)`, care doar scrie pe
   înregistrarea de progres, în același cursor.
3. Statusul se decide după ce citește `progress.done` și `progress.remaining`:

| Rezultat callback | `done` | `remaining` | Status | Ce urmează |
|---|---|---|---|---|
| OK | oricât | 0 | `FULLY_DONE` | ieșire din buclă → `_reschedule_later` |
| OK | **0** | > 0 | `FULLY_DONE` (!) | Odoo presupune că acțiunea nu folosește API-ul de progres și **oprește** bucla |
| OK | > 0 | > 0 | `PARTIALLY_DONE` | **iterația următoare imediat**, în același worker și cursor |
| excepție | > 0 (commis) | > 0 (commis) | `PARTIALLY_DONE` | continuă bucla |
| excepție | altfel | | `FAILED` | ieșire, `failure_count += 1` |

4. După 10 iterații tot `PARTIALLY_DONE`, `_process_job` apelează `_reschedule_asap`, care
   nu face nimic intenționat: `nextcall` și trigger-ele rămân în trecut, deci job-ul rămâne
   „ready”. Este preluat la următorul poll al worker-ului: după aproximativ
   `SLEEP_INTERVAL`, imediat dacă `ODOO_NOTIFY_CRON_CHANGES` e setat, sau de alt worker
   cron. **Nu e nevoie de `_trigger()`.**
5. `FULLY_DONE` sau `FAILED` → `_reschedule_later`: `nextcall` sare la următorul interval,
   iar trigger-ele trecute se șterg.

Concluzie pentru `remaining > 0`: cron-ul se reia **imediat, de maximum 10 ori la o preluare**.
Apoi rămâne gata de rulare și se reia la următorul poll, până când `remaining == 0`
sau `done == 0`. Între iterații nu există nicio pauză.

### 1.3 Timeout (`timed_out_counter`)

- Contorul se incrementează **înainte** de callback și se face commit. Dacă procesul e omorât
  (`limit_time_real_cron`/`limit_time_real` sau limita platformei Odoo.sh), înregistrarea de
  progres rămâne cu contorul mărit și `done = 0`.
- La următoarea preluare, `_acquire_one_job` citește ultimul progres. Dacă
  `timed_out_counter >= 3` **și** `done == 0`, rularea **nu se mai execută**: e marcată
  `FAILED`, contorul se resetează, iar `failure_count` crește. După 5 eșecuri pe o perioadă
  de cel puțin 7 zile, cron-ul se dezactivează și adminul e notificat (`_notify_admin`).
- Protecția vine din `done > 0` comis: un cron care notifică progresul **și face commit** în
  timpul lotului nu e considerat eșuat la timeout. Dacă nu face commit, scrierea în
  `ir.cron.progress` se pierde odată cu tranzacția.
- Mecanismul acesta se aplică tuturor cron-urilor, chiar și celor care nu folosesc
  `_notify_progress`.

### 1.4 `deactivate=True`

Contează doar dacă statusul e `FULLY_DONE`: `job['active'] = False` se scrie prin
`_update_failure_count`. Este util la cron-urile de migrare one-shot, de exemplu
`l10n_ro_vat_change`.

### 1.5 „Run manually” (`method_direct_trigger`) în v18

- **Are** `ir_cron_progress_id` în context, pentru că apelează `_add_progress()`. Prin urmare
  `_notify_progress` scrie progresul, dar acțiunea **rulează o singură dată**: nu există buclă
  și nici reprogramare.
- **Nu are** `cron_id` în context. Cheia `cron_id` e pusă doar de `_run_job`, deci se poate
  folosi ca să deosebim rularea manuală de cea din worker.
- Consecință importantă: azi, la „Run manually”, `_trigger()` pune restul în fundal. După
  trecerea pe progres, **restul lotului ar aștepta până la următorul `nextcall`**, adică a doua
  zi la cron-urile zilnice. Același lucru se întâmplă la
  `deltatech_cron_monitor_webhook` (`controllers/webhook_controller.py:54`), care apelează
  `method_direct_trigger()`. Pattern-ul recomandat mai jos tratează acest caz.
- Apelul direct din cod sau din teste nu are progres în context, deci `_notify_progress` nu
  face nimic. Este sigur.

### 1.6 Diferențe în 19.0 (compatibilitate la migrare)

Sursa: `/Users/dhongu/Odoo/odoo19/odoo/odoo/addons/base/models/ir_cron.py`.

- `_notify_progress` există încă, dar e **`@api.deprecated("Since 19.0, use _commit_progress")`**
  și are `assert progress.cron_id.id == context['cron_id']`.
- Apare `_commit_progress(processed, *, remaining=None, deactivate=False)`. Acesta
  **adună** `processed` la `done`, face **commit**, returnează timpul rămas
  (`cron_end_time - now`) și, în afara cron-ului, face doar commit.
- Bucla nu mai are maximum 10 iterații: rulează cât timp `loop_count < MIN_RUNS_PER_JOB (10)`
  **sau** `time < cron_end_time (start + 10 s)`. Adică face cel puțin 10 rulări și cel puțin
  10 secunde.
- **Diferență critică:** în v19, `done == 0` cu `remaining > 0` la prima iterație înseamnă
  `PARTIALLY_DONE` (cu warning „processed no record”), deci reluare ASAP, nu oprire ca în v18.
  Un cron care raportează mereu `remaining > 0` fără să avanseze (înregistrări care nu se
  pot procesa, `dry_run`) **devine buclă infinită în v19**. Regula de aur pentru ambele
  versiuni: **dacă lotul nu a avansat, raportează `remaining=0`.**
- `method_direct_trigger` din v19 rulează ca scheduler-ul, cu buclă. Ramura de rezervă cu
  `_trigger()` din pattern-ul de mai jos nu strică nimic acolo.

---

## 2. Inventar

### 2.1 Cron-uri care se repornesc singure cu `_trigger()`

| # | Fișier:linie | Modul | Ce face | Cum știe că „mai e de lucru” | Recomandare |
|---|---|---|---|---|---|
| A1 | `odoo-addons/deltatech/deltatech_actions/models/res_partner.py:58` | deltatech_actions | Unește contactele duplicate după email (câte 10 grupuri) | SQL `GROUP BY email HAVING count>1 LIMIT limit+1` | **DA, prioritar.** `remaining` = `SELECT count(*) FROM (…GROUP BY… HAVING…)`, ieftin |
| A2 | `…/deltatech_actions/models/res_partner.py:101` | deltatech_actions | Unește companiile duplicate după CUI | idem, `GROUP BY vat` | **DA, prioritar**, identic cu A1 |
| B1 | `odoo-addons/terrabit/l10n_ro_vat_change/models/res_company.py:75` (copii identice în `proiecte/ancopolar/…:77` și `proiecte/100PRO/…:77`) | l10n_ro_vat_change | Înlocuiește taxele 5/9/19 → 11/21 pe produse, câte 1000 pe tip de taxă | `search(limit=1001)` pe fiecare taxă sursă | **DA.** `remaining` = `search_count` cu un singur domeniu `taxes_id in src \| supplier_taxes_id in src`. În plus, `deactivate=True` la final, fiindcă e un cron one-shot. Prioritate mică: schimbarea TVA a rulat deja (august 2025) |
| C1 | `odoo-addons/deltatech/deltatech_queue_job/models/queue_job.py:227` (`_job_runner`) | deltatech_queue_job | Runner intern queue_job: procesează `batch_size` joburi (20) într-un buget de `max_seconds` (50 s) | `search(limit=batch+1)` sau buget de timp depășit | **DA, cu grijă.** `remaining` = `search_count(domain pending)`. Risc: 10 iterații × 50 s pot ajunge la ~500 s pe o singură preluare, ceea ce contrazice scopul declarat al modulului („preventing worker timeouts on Odoo.sh”). Vezi §4 |
| D1 | `proiecte/diginesis/deltatech_delivery/models/delivery.py:425` | deltatech_delivery (diginesis) | Sincronizează statusul AWB la curieri, câte 50 | `search(limit+1)`; reprogramare la **+5 min** | **Parțial.** Ramura de backlog poate trece pe progres (`history_date` e scris, deci lotul avansează). Pauza de 5 min ține însă API-urile curierilor sub limită. Recomand să rămână `_trigger(at)`, plus `_notify_progress(done, remaining=0)` doar pentru log |
| D2 | `…/deltatech_delivery/models/delivery.py:428` | idem | Polling la 30 min pentru colete în tranzit | `search_count(limit=1)` | **NU.** Întârzierea face parte din logică |
| E1 | `odoo-addons/l10n-romania/l10n_ro_efactura_enhancement/models/account_move.py:109` | l10n_ro_efactura_enhancement | Preia statusul facturilor din SPV (câte 20), reluare la **+2 min** | `need_retrigger = True` oricând găsește facturi `invoice_sent`, chiar dacă nu s-a schimbat nimic | **NU** (ANAF e asincron, iar pauza e necesară). Observație separată: retrigger-ul la 2 min continuă cât timp există o factură `invoice_sent` în ultimele 30 de zile, chiar dacă ANAF nu răspunde. Merită legat de `len(invoices) == limit` sau de un progres real (stare schimbată) |
| E2 | `…/account_move.py:323` | idem | Trimite facturile în SPV (câte 20), reluare la **+5 min** | `len(candidates) > limit` (exact) | **NU** pentru reluare. Pauza lasă SPV să proceseze, iar facturile eșuate (`allow_raising=False`) rămân candidate: cu reluare imediată ar fi retrimise în rafală până la `MAX_SPV_SEND_RETRIES`. Opțional: `_notify_progress(done=len(invoices), remaining=0)` pentru log. Atenție: `_cron_l10n_ro_edi_auto_send` apelează intern `_cron_l10n_ro_edi_fetch_status`. Dacă ambele notifică progresul, a doua suprascrie progresul primeia (același `ir_cron_progress_id`) |

### 2.2 `_trigger()` declanșat de evenimente (nu e retrigger de lot, nu intră în refactorizare)

| Fișier:linie | Ce face |
|---|---|
| `odoo-addons/deltatech/deltatech_queue_job/models/queue_job.py:232–276` (`_cron_trigger`) | Programează runner-ul la ETA-ul joburilor, cu debounce. Rămâne așa |
| `proiecte/diginesis/deltatech_marketplace*/…` (`sale_order.py:175`, `stock_picking.py:32`, `wizard/sync_product.py:129`, `backend.py:848`, `stock_move.py:16`, `controller/main.py:144`) | Pornește runner-ul queue_job după ce pune joburi în coadă |
| `proiecte/diginesis/deltatech_marketplace/models/binding_product.py:109`, `binding_product_template.py:82` | Pornește exportul de preț după editarea unui preț |
| `proiecte/romsystems/terrabit_rsy/models/stock_picking.py:79` | Rulează scheduler-ul de stoc după recepție |
| `odoo-addons/deltatech/deltatech_cron_monitor_webhook/controllers/webhook_controller.py:54` | `method_direct_trigger()` din webhook. Nu e `_trigger`, dar e relevant: vezi §1.5 |

### 2.3 Cron-uri pe loturi fără retrigger, care ar beneficia de progres

| # | Fișier:linie | Modul | Ce face | `remaining` | Recomandare / risc |
|---|---|---|---|---|---|
| F1 | `odoo-addons/deltatech/deltatech_actions/models/res_partner.py:102–220` (`cron_normalize_company_names`) | deltatech_actions | Normalizează sufixele SRL/SA/PFA/II | `COUNT(*)` cu regex | **Mai întâi bug-ul, apoi progresul.** `offset` e mereu 0, iar regex-ul se potrivește și pe forma deja normalizată („S.R.L.”). Lotul actualizează mereu aceleași prime 500 de id-uri și `total_companies` nu scade niciodată. Cu progres, ar deveni buclă la fiecare preluare. Este nevoie de un predicat „încă nenormalizat” (exclus `' (S\.R\.L\.\|S\.A\.\|P\.F\.A\.\|I\.I\.)$'` case-sensitive). În plus, `message_post` către toți adminii ar trebui trimis doar la `remaining == 0` |
| F2 | `…/deltatech_actions/models/mail_message.py:19` (`cron_clean_old_messages`) | deltatech_actions | Șterge mesajele vechi, câte 5000 | `count` pe același `WHERE` | **DA, cu condiții:** `remaining=0` când `dry_run=True` (valoarea implicită în XML!) sau când `unlink` a eșuat (`except: log`). Altfel apare buclă în v19 |
| F3 | `…/deltatech_actions/models/account_move.py:66`, `sale_order.py:43`, `stock_picking.py:19` (`cron_clean_generated_pdfs`) | deltatech_actions | Șterge PDF-urile generate, câte 5000 | `count` pe același `WHERE` | **DA**, cu aceleași condiții ca F2 (`dry_run` și eșec la `unlink`) |
| F4 | `…/deltatech_actions/models/account_move.py:19` (`cron_clean_xml_attachments`) | deltatech_actions | Șterge XML-urile duplicate | greu: grupurile cu atașamente legate de `edi_document_ids` rămân mereu „duplicate” | **NU** (un `remaining` corect e scump, iar unele grupuri nu pot fi niciodată epuizate) |
| F5 | `odoo-addons/deltatech/deltatech_image_optimize/models/ir_attachment.py:304` | deltatech_image_optimize | Recomprimă imaginile, câte 50 (originale + variante), apoi rulează GC pe filestore | `search_count` pe cele două domenii (`deltatech_image_optimized = False`) | **DA, valoare mare** (50/zi e prea puțin pe cataloage mari). Condiții: `_gc_file_store()` doar la `remaining == 0`, nu la fiecare iterație. `remaining` trebuie să excludă atașamentele la care `write` a eșuat (azi rămân nemarcate și ar fi reluate la nesfârșit). `search_count` pe `ir_attachment` cere un index pe `deltatech_image_optimized`, de verificat |
| F6 | `odoo-addons/deltatech/deltatech_invoice_picking_automatically/models/stock_picking.py:39` | deltatech_invoice_picking_automatically | Facturează automat livrările, câte 100 pe zi | `search_count([("invoice_state","=","to_invoice")])` | **DA.** Eșecurile devin `failed`, deci lotul avansează. Observație separată: `except` fără `savepoint`, iar o eroare SQL lasă cursorul inutilizabil pentru restul lotului |
| F7 | `odoo-addons/deltatech/deltatech_alternative/models/product.py:233` (`split_multi_codes`) | deltatech_alternative | Sparge codurile alternative multiple, câte 5000 | `search_count(domain)` | **DA.** Atenție: un nume format doar din separatori (`codes == []`) rămâne în domeniu pentru totdeauna, deci trebuie exclus din `remaining` |
| F8 | `proiecte/romsystems/terrabit_product_prices/models/product_template.py:51` (`cron_compute_sale_prices`) | terrabit_product_prices | Recalculează prețurile de vânzare, câte 1000 pe oră, în cicluri | `total_remaining` e deja calculat | **Opțional.** Încărcarea pare distribuită intenționat pe ore (`hour_from/hour_to`). Dacă se trece pe progres, `remaining` nu trebuie să includă resetarea ciclului, altfel cron-ul nu se mai oprește |
| F9 | `proiecte/uportho/custom_modules/uportho_auto_translate/models/product_template.py:119` | uportho_auto_translate | Traduce prin API plătit, are buget de timp și cursor | greu (cursor + „ce mai e de tradus”) | **NU.** Cost API și reluare controlată de buget. Cel mult `_notify_progress(done=n, remaining=0)` pentru log |
| — | `deltatech_website_sale_sort/models/product.py:63` | | Împarte deja în joburi `with_delay()` | — | NU e cazul |

---

## 3. Ce câștigăm și ce riscăm

**Câștiguri**
- Linia nativă în log `Job 'X' processed N records, M remaining` la fiecare iterație, plus
  istoricul în `ir.cron.progress`, păstrat 1 săptămână.
- Fără `ir.cron.trigger` creat la fiecare lot și fără `env.ref(...)` hardcodat în metodă.
  Același cod merge și pentru o copie a cron-ului, cu alți parametri.
- Până la 10 loturi într-o singură preluare, fără așteptarea poll-ului (~60 s) între loturi.
- Protecție la timeout: cu commit după `_notify_progress`, un timeout după progres nu se mai
  socotește eșec și nu duce la dezactivarea cron-ului.
- `deactivate=True` pentru cron-urile one-shot.
- Când cron-ul nu mai avansează (`done == 0`), v18 îl oprește singur. Azi, unele `_trigger()`
  pot cicla la nesfârșit (vezi E1, F1).

**Riscuri**
1. **Întârziere intenționată.** Progresul nu știe să aștepte. E1, E2, D1 și D2 rămân pe `_trigger(at)`.
2. **„Run manually” și webhook-ul** rulează un singur lot în v18 (§1.5). Se rezolvă cu
   ramura de rezervă `_trigger()` când lipsește `cron_id` din context.
3. **Durata unei preluări crește** de până la 10 ori: worker-ul de cron e ținut ocupat, iar
   alte cron-uri gata de rulare așteaptă. Pe Odoo.sh, întreaga trecere `_process_jobs` pe o
   bază trebuie să încapă în limita worker-ului. Loturile trebuie dimensionate astfel încât
   10 loturi să încapă confortabil în limită, sau trebuie trimis `remaining=0` după un
   buget de timp propriu.
4. **`remaining` care nu scade** (`dry_run`, înregistrări imposibil de procesat, erori
   înghițite de `except`) e inofensiv în v18 (`done=0` → oprire), dar devine **buclă infinită
   în v19**.
5. **Cron apelat din alt cron sau din alt loc** (E2 → E1, teste, butoane): `_notify_progress`
   din metoda apelată suprascrie progresul apelantului. Progresul trebuie notificat doar în
   punctul de intrare al cron-ului.
6. **`remaining` scump.** `COUNT` pe `GROUP BY` sau pe `ir_attachment` mare costă la fiecare
   iterație. Dacă e prea scump, se poate folosi `remaining = 1 if len(lot) == limit else 0`
   (euristica „limit+1” deja folosită). Pierdem doar cifra exactă din log.

---

## 4. Pattern recomandat (v18, compatibil cu migrarea la v19)

```python
def _cron_merge_duplicate_contacts(self, limit=10):
    groups = self._get_duplicate_contact_groups(limit)  # SQL cu LIMIT %s
    done = 0
    for email, ids in groups:
        try:
            with self.env.cr.savepoint():
                self._merge_partner_group(ids, email)
            done += 1
        except Exception:
            _logger.exception("Merge failed for %s", email)
    remaining = self._count_duplicate_contact_groups() if done else 0
    self._cron_report_progress("deltatech_actions.ir_cron_merge_contacts", done, remaining)


@api.model
def _cron_report_progress(self, cron_xmlid, done, remaining):
    """Raportează progresul unui lot; reia cron-ul și la rularea manuală."""
    cron = self.env["ir.cron"]
    if not done:
        remaining = 0  # nu am avansat: oprește bucla (obligatoriu în v19)
    cron._notify_progress(done=done, remaining=remaining)
    if remaining and not self.env.context.get("cron_id"):
        # rulare manuală / webhook / apel direct: v18 nu reia singur
        self.env.ref(cron_xmlid)._trigger()
    return float("inf")  # aceeași semnătură ca în 19.0, unde e timpul rămas din felie
```

Varianta pentru 19.0 se află în `/Users/dhongu/Odoo/odoo19/odoo-addons/deltatech/deltatech_actions/readme/ANALIZA_CRON_PROGRESS.md` (§3).

Reguli:
- Notifici **o singură dată, la final**, în metoda de intrare a cron-ului. Dacă lotul face
  commit intermediar, notifici și înainte de fiecare commit, ca progresul să supraviețuiască
  unui timeout.
- `done` reprezintă ce s-a procesat **în acest lot**, nu un total cumulat. v18 nu adună
  valorile.
- `remaining=0` când `done == 0`, la `dry_run`, sau când restul nu poate fi procesat.
- Helper-ul `_cron_report_progress` merită pus într-un singur loc (de exemplu un mixin în
  `deltatech`) ca să fie folosit peste tot. La migrarea pe 19.0 se schimbă doar corpul lui:
  `cron._commit_progress(done, remaining=remaining)`, iar ramura de rezervă poate rămâne.
- Pentru cron-urile cu buget de timp (C1), în v18 trimiți `remaining=0` după un buget total
  propriu, ținut în context sau în `ir.config_parameter`, ca să nu legi 10 × `max_seconds`.
  În v19 folosești valoarea returnată de `_commit_progress`.

---

## 5. Ordinea propusă pentru refactorizare

1. **Helper-ul comun** `_cron_report_progress` (§4), cu test unitar pe trei cazuri: în cron
   (context cu `cron_id` + `ir_cron_progress_id`), la rulare manuală (doar progres) și la
   apel direct.
2. **A1 + A2** (`deltatech_actions`, merge contacte/companii): cazul de referință, cu
   `remaining` ieftin și teste existente (`tests/test_res_partner.py`). Tot aici: un
   `savepoint` pe grup, ca un merge eșuat să nu anuleze lotul.
3. **F2 + F3** (curățarea mesajelor și a PDF-urilor), tot în `deltatech_actions`: tratezi
   `dry_run` și eșecul la `unlink`.
4. **F5** (`deltatech_image_optimize`), unde câștigul e cel mai mare: GC-ul rulează doar la
   final și verifici indexul.
5. **F6, F7** (facturare automată, coduri alternative).
6. **C1** (`deltatech_queue_job._job_runner`), după ce stabilești bugetul total pe preluare.
   Se testează pe un client Odoo.sh.
7. **F1**, după corectarea bug-ului cu `offset`/regex (separat, înainte de progres).
8. **B1** (`l10n_ro_vat_change`), doar dacă modulul mai e instalat undeva; altfel, de lăsat așa.
9. **D1** și **E2**: doar log (`remaining=0`), păstrând `_trigger(at)`. **E1**: corectezi
   condiția de retrigger (observația din tabel), fără progres.

Fără schimbare: D2, F4, F8 (decizie de business), F9 și toate trigger-ele de eveniment din §2.2.
