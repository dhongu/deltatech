# Unificarea partenerilor duplicați pe CUI

Set de scripturi pentru unificarea în masă a fișelor de parteneri care împart același CUI, fără a dezactiva cheile
străine și fără drepturi de superuser (merge și pe odoo.sh).

## De ce nu wizardul standard și nu `session_replication_role`

Wizardul Odoo (`base.partner.merge.automatic.wizard`) rulează `_update_foreign_keys` **per grup**: la ~4.800 de grupuri
× ~158 de coloane FK înseamnă peste 750.000 de instrucțiuni UPDATE. Nu se termină într-o fereastră rezonabilă.

Tentația următoare e `SET session_replication_role = replica` (dezactivează verificarea FK). Costă superuser —
indisponibil pe odoo.sh — și mută răspunderea integrității de pe bază pe autorul scriptului. Nu e necesar: **lentoarea
nu vine de la verificarea FK în sine, ci de la coloanele FK neindexate.** `res_partner` e referit de ~158 de coloane,
din care ~77 nu aveau index; fără index, fiecare ștergere declanșează scanări secvențiale complete (măsurat: 3.180 MB
scanați per rând).

Abordarea de aici: creează indexurile (pasul 01), apoi inversează buclele — un singur UPDATE per coloană pentru tot
lotul, în loc de unul per grup per coloană.

## Măsurători pe o bază de producție (peste 500.000 de parteneri)

Lot complet A + B: **4.800 de grupuri, 5.350 de fișe absorbite.**

| Etapă                                               | Timp            |
| --------------------------------------------------- | --------------- |
| Creare 77 indexuri (`CONCURRENTLY`)                 | ~4 s, 1.222 MB  |
| Dedup coliziuni unique pe coloanele FK              | ~1 s            |
| Remap 158 coloane FK + `parent_id` (95.023 rânduri) | 69,4 s          |
| Dedup coliziuni pe `res_id` (3.703 rânduri)         | ~1 s            |
| Remap legături polimorfe (4.675 rânduri)            | 2,1 s           |
| Completare câmpuri goale pe masteri (889)           | <1 s            |
| **DELETE 5.350 fișe, cu FK ACTIVE**                 | **189,7 s**     |
| **Total**                                           | **~4,5 minute** |

Pentru comparație, aceeași ștergere fără indexuri a depășit 8 minute fără să termine.

## Rulare

```bash
# 1. Indexurile (o singură dată, se poate rula în timpul programului)
psql -d <bd> -f 01_fk_indexes.sql

# 2. Construiește lotul (fără efect asupra datelor de business)
psql -d <bd> -v categorii="'A','B'" -v limita_grupuri=200 -f 02_build_map.sql

# 3. Simulare — rulează tot fluxul, apoi ROLLBACK
psql -d <bd> -f 03_merge.sql

# 4. Aplicare, după ce simularea arată curat
psql -d <bd> -v do_apply=1 -f 03_merge.sql

# 5. Verificare
psql -d <bd> -f 04_verify.sql
```

Parametri utili:

- `-v limita_grupuri=0` — tot lotul (implicit 200)
- `-v arhiveaza=1` — `active = false` în loc de ștergere (recomandat la primele loturi)
- `-v categorii="'A'"` — doar categoria cea mai sigură

## Categoriile de grupuri

| Cat. | Descriere                                          | Tratament                     |
| ---- | -------------------------------------------------- | ----------------------------- |
| A    | o singură față are documente, restul complet goale | automat                       |
| B    | documente doar pe o față                           | automat                       |
| C    | facturi pe mai multe fețe                          | manual, cu contabilitatea     |
| D    | sold nereconciliat pe mai multe fețe               | manual, după închiderea lunii |

Pasul 02 exclude automat din lot grupurile care: conțin compania proprie, au user portal pe mai multe fețe, sau au
denumiri complet divergente (revizuire manuală — vezi mai jos).

## Capcane confirmate prin testare

**NULL nu produce coliziune într-un index unique.** `PARTITION BY` însă grupează toate NULL-urile la un loc. Fără
filtrul `k IS NOT NULL`, dedup-ul a marcat ca duplicate toți vizitatorii anonimi de site (`website_visitor.partner_id`
unique, majoritar NULL) — **181.583 de rânduri șterse eronat**, fără nicio eroare. Clasa asta de bug nu se vede decât
rulând.

**Odoo are două convenții polimorfe:** `(res_model, res_id)` pentru `mail.activity`, `ir.attachment`, `mail.followers`,
`rating.rating`; dar `(model, res_id)` pentru `mail.message` și `ir.model.data`. Tratarea doar a primeia lasă chatterul
agățat de fișe șterse.

**Dedup-ul se face pe valoarea ȚINTĂ, nu comparând fișa absorbită cu masterul.** Două fișe din același grup se pot
ciocni între ele după remap, fără ca masterul să fie implicat. Și trebuie recalculat după fiecare etapă de remap:
remapul lui `partner_id` creează coliziuni pe `res_id` care nu existau la începutul tranzacției. Constrângerile unique
rămân active și sub `session_replication_role = replica` — bypass-ul de FK nu acoperă acest pas.

**Masterul e ales după documente, nu după calitatea denumirii.** Uneori supraviețuiește fișa cu numele prost formatat.
Pasul 04, secțiunea E, listează masterii cu denumire suspectă, de corectat manual după merge.

**`mobile` nu mai există pe `res.partner` în Odoo 19.**

## Înainte de producție

- Rulează întâi pe staging, cap-coadă, cu `04_verify.sql` curat.
- Backup / PITR confirmat înainte de rularea cu `do_apply=1`.
- Validează cu clientul regula de master pe un eșantion de ~20 de grupuri.
- Primele loturi mici (`limita_grupuri=50`) și, dacă vrei plasă de siguranță, `arhiveaza=1`.
- Indexurile de la pasul 01 rămân permanent și accelerează orice ștergere sau arhivare de partener de aici înainte.
  Patru dintre cele mai scumpe coloane sunt din modulele noastre (`l10n_ro_transport_partner_id`,
  `l10n_ro_etransport_start_address`, `delegate_id`) — merită `index=True` în cod, ca să nu revină problema la fiecare
  instalare nouă.
