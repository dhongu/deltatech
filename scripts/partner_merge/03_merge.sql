-- =============================================================================
-- 03 — Execuția unificării pentru lotul din pm_map
-- =============================================================================
-- Principiu: NU dezactivăm cheile străine (fără session_replication_role, deci
-- fără superuser — merge și pe odoo.sh). Inversăm buclele față de wizardul Odoo:
-- un singur UPDATE per coloană pentru TOT lotul, în loc de un UPDATE per grup
-- per coloană. Integritatea rămâne verificată de bază.
--
-- Ordinea contează:
--   1. dedup coliziuni unique pe coloanele FK   (calculat pe valoarea ȚINTĂ)
--   2. remap coloane FK + parent_id
--   3. dedup coliziuni unique pe res_id          (RECALCULAT — pasul 2 a schimbat datele)
--   4. remap legături polimorfe (res_model/res_id) + ir_model_data
--   5. completare câmpuri goale pe master (opțional)
--   6. ștergerea sau arhivarea fișelor absorbite
--
-- Dedup-ul colapsează pe valoarea ȚINTĂ, nu comparând fișa absorbită cu masterul:
-- două fișe din același grup se pot ciocni ÎNTRE ELE după remap, fără ca masterul
-- să fie implicat. Constrângerile unique rămân active și sub replica, deci acest
-- pas e obligatoriu indiferent de abordare.
--
-- Rulare:
--   psql -d <bd> -f 03_merge.sql                    -- SIMULARE: rulează tot, apoi ROLLBACK
--   psql -d <bd> -v do_apply=1 -f 03_merge.sql      -- APLICĂ (COMMIT)
--   psql -d <bd> -v do_apply=1 -v arhiveaza=1 -f 03_merge.sql
-- Parametri:
--   do_apply    0 = simulare cu rollback (implicit), 1 = commit
--   arhiveaza   0 = șterge fișele absorbite (implicit), 1 = doar active=false
--
-- Necesită: 02_build_map.sql rulat (tabelele pm_map / pm_face).
-- Recomandat: 01_fk_indexes.sql rulat înainte, altfel pasul 6 durează ore.
-- =============================================================================
\timing on
\set ON_ERROR_STOP on
\if :{?do_apply}  \else \set do_apply 0  \endif
\if :{?arhiveaza} \else \set arhiveaza 0 \endif

BEGIN;

-- Funcție de dedup generică: pentru fiecare index UNIQUE care conține o coloană
-- ce va fi remapată, colapsează rândurile care ar deveni identice după remap.
-- p_mode = 'fk'   -> coloana remapată e o coloană FK spre res_partner
-- p_mode = 'poly' -> coloana remapată e res_id (cu res_model = 'res.partner')
CREATE OR REPLACE FUNCTION pg_temp.pm_dedupe_unique(p_mode text) RETURNS TABLE(tabela text, sterse bigint) AS $fn$
DECLARE
  r RECORD; key_expr text; n bigint; where_cl text;
BEGIN
  FOR r IN
    SELECT c.relname AS tbl, i.indexrelid, i.indrelid AS indrelid_tbl,
           (SELECT array_agg(att.attname ORDER BY k.ord)
              FROM unnest(i.indkey::int[]) WITH ORDINALITY k(attnum, ord)
              JOIN pg_attribute att ON att.attrelid = i.indrelid AND att.attnum = k.attnum) AS cols,
           tgt.col AS remap_col
    FROM pg_index i
    JOIN pg_class c ON c.oid = i.indrelid AND c.relkind = 'r' AND c.relnamespace = 'public'::regnamespace
    JOIN LATERAL (
      SELECT a.attname AS col
      FROM pg_attribute a
      WHERE a.attrelid = i.indrelid AND a.attnum > 0 AND NOT a.attisdropped
        AND (
          (p_mode = 'fk' AND EXISTS (
             SELECT 1 FROM pg_constraint fc
             JOIN pg_attribute fa ON fa.attrelid = fc.conrelid AND fa.attnum = ANY(fc.conkey)
             WHERE fc.contype = 'f' AND fc.confrelid = 'res_partner'::regclass
               AND fc.conrelid = i.indrelid AND fa.attname = a.attname))
          OR
          (p_mode = 'poly' AND a.attname = 'res_id'
           AND EXISTS (SELECT 1 FROM pg_attribute a2 WHERE a2.attrelid = i.indrelid
                         AND a2.attname IN ('res_model', 'model') AND NOT a2.attisdropped))
        )
      LIMIT 1
    ) tgt ON true
    WHERE i.indisunique AND i.indisvalid AND i.indpred IS NULL
      AND tgt.col = ANY (SELECT att.attname FROM unnest(i.indkey::int[]) k(attnum)
                          JOIN pg_attribute att ON att.attrelid = i.indrelid AND att.attnum = k.attnum)
      AND c.relname <> 'res_partner'
  LOOP
    -- cheia de partiționare = coloanele indexului, cu coloana remapată înlocuită de ținta ei
    SELECT string_agg(
             CASE WHEN col = r.remap_col
                  THEN format('COALESCE(m.master_id, x.%I)', col)
                  ELSE format('x.%I', col) END, ', ' ORDER BY ord)
      INTO key_expr
      FROM unnest(r.cols) WITH ORDINALITY AS u(col, ord);

    IF p_mode = 'poly' THEN
      where_cl := format('WHERE x.%I = ''res.partner''',
        (SELECT a2.attname FROM pg_attribute a2
          WHERE a2.attrelid = r.indrelid_tbl AND a2.attname IN ('res_model','model') AND NOT a2.attisdropped
          ORDER BY CASE a2.attname WHEN 'res_model' THEN 0 ELSE 1 END LIMIT 1));
    ELSE
      where_cl := '';
    END IF;

    EXECUTE format($q$
      WITH t AS (
        SELECT x.ctid AS cid, ROW(%s) AS k
        FROM %I x LEFT JOIN pm_map m ON m.old_id = x.%I
        %s
      ), dup AS (
        -- k IS NOT NULL pe un ROW() e adevărat doar când TOATE câmpurile sunt non-null.
        -- Obligatoriu: în PostgreSQL, NULL nu produce coliziune într-un index unique, dar
        -- PARTITION BY grupează toate NULL-urile la un loc. Fără filtrul ăsta, un index de
        -- tip website_visitor_partner_uniq (partner_id) ar face ca toți vizitatorii anonimi
        -- (partner_id NULL) să pară duplicate între ei — măsurat: 181.583 rânduri șterse eronat.
        SELECT cid, row_number() OVER (PARTITION BY k ORDER BY cid) AS rn
        FROM t
        WHERE k IS NOT NULL
          AND k IN (SELECT k FROM t WHERE k IS NOT NULL GROUP BY k HAVING count(*) > 1)
      )
      DELETE FROM %I WHERE ctid IN (SELECT cid FROM dup WHERE rn > 1)
    $q$, key_expr, r.tbl, r.remap_col, where_cl, r.tbl);
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n > 0 THEN tabela := r.tbl; sterse := n; RETURN NEXT; END IF;
  END LOOP;
END$fn$ LANGUAGE plpgsql;

\echo ''
\echo '== 1. Dedup coliziuni unique pe coloanele FK =='
SELECT * FROM pg_temp.pm_dedupe_unique('fk');

\echo ''
\echo '== 2. Remap coloane FK + parent_id =='
DO $$
DECLARE r RECORD; n bigint; total bigint := 0; t0 timestamptz := clock_timestamp();
BEGIN
  FOR r IN SELECT c.conrelid::regclass::text AS tbl, a.attname AS col
           FROM pg_constraint c
           JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
           WHERE c.contype = 'f' AND c.confrelid = 'res_partner'::regclass
             AND c.conrelid::regclass::text <> 'res_partner'
  LOOP
    EXECUTE format('UPDATE %s t SET %I = m.master_id FROM pm_map m WHERE t.%I = m.old_id', r.tbl, r.col, r.col);
    GET DIAGNOSTICS n = ROW_COUNT; total := total + n;
  END LOOP;
  UPDATE res_partner p SET parent_id = m.master_id FROM pm_map m WHERE p.parent_id = m.old_id;
  GET DIAGNOSTICS n = ROW_COUNT; total := total + n;
  RAISE NOTICE 'remap FK + parent_id: % rânduri în % s', total, round(extract(epoch from clock_timestamp() - t0), 1);
END$$;

\echo ''
\echo '== 3. Dedup coliziuni unique pe res_id (recalculat după pasul 2) =='
SELECT * FROM pg_temp.pm_dedupe_unique('poly');

\echo ''
\echo '== 4. Remap legături polimorfe =='
-- Odoo folosește DOUĂ convenții pentru legăturile polimorfe:
--   (res_model, res_id) — mail.activity, ir.attachment, mail.followers, rating.rating...
--   (model,     res_id) — mail.message, ir.model.data
-- Ambele trebuie acoperite; tratarea doar a primeia lasă în urmă mesajele din chatter
-- (măsurat: 87 de rânduri orfane în mail_message la primul test).
DO $$
DECLARE r RECORD; n bigint; total bigint := 0; t0 timestamptz := clock_timestamp();
BEGIN
  FOR r IN
    SELECT t.table_name,
           (SELECT c.column_name FROM information_schema.columns c
             WHERE c.table_schema='public' AND c.table_name=t.table_name
               AND c.column_name IN ('res_model','model')
             ORDER BY CASE c.column_name WHEN 'res_model' THEN 0 ELSE 1 END LIMIT 1) AS model_col
    FROM information_schema.tables t
    WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
      AND EXISTS (SELECT 1 FROM information_schema.columns c
                   WHERE c.table_schema='public' AND c.table_name=t.table_name AND c.column_name='res_id')
      AND EXISTS (SELECT 1 FROM information_schema.columns c
                   WHERE c.table_schema='public' AND c.table_name=t.table_name
                     AND c.column_name IN ('res_model','model')
                     AND c.data_type IN ('character varying','text'))
  LOOP
    EXECUTE format('UPDATE %I t SET res_id = m.master_id FROM pm_map m WHERE t.%I = ''res.partner'' AND t.res_id = m.old_id',
                   r.table_name, r.model_col);
    GET DIAGNOSTICS n = ROW_COUNT; total := total + n;
  END LOOP;
  RAISE NOTICE 'remap polimorfic: % rânduri în % s', total, round(extract(epoch from clock_timestamp() - t0), 1);
END$$;

\echo ''
\echo '== 5. Completarea câmpurilor goale pe master =='
-- Doar câmpuri de contact GOALE pe master, luate de la cea mai recentă fișă absorbită
-- care le are completate. Nu suprascrie niciodată o valoare existentă pe master.
DO $$
DECLARE r RECORD; n bigint; total bigint := 0;
BEGIN
  -- Notă: `mobile` nu mai există pe res.partner în Odoo 19.
  FOR r IN SELECT unnest(ARRAY['email','phone','website','street','street2','city','zip','function']) AS col
  LOOP
    EXECUTE format($q$
      UPDATE res_partner mst SET %I = src.val
      FROM (
        SELECT DISTINCT ON (m.master_id) m.master_id, o.%I AS val
        FROM pm_map m JOIN res_partner o ON o.id = m.old_id
        WHERE o.%I IS NOT NULL AND o.%I <> ''
        ORDER BY m.master_id, o.write_date DESC
      ) src
      WHERE mst.id = src.master_id AND (mst.%I IS NULL OR mst.%I = '')
    $q$, r.col, r.col, r.col, r.col, r.col, r.col);
    GET DIAGNOSTICS n = ROW_COUNT; total := total + n;
  END LOOP;
  RAISE NOTICE 'câmpuri completate pe masteri: %', total;
END$$;

\echo ''
\echo '== 6. Ștergerea / arhivarea fișelor absorbite =='
-- Notă: psql NU substituie variabile în interiorul blocurilor $$...$$,
-- de aceea ramificarea se face aici, la nivel de \if, nu în plpgsql.
\if :arhiveaza
  DO $$
  DECLARE n bigint; t0 timestamptz := clock_timestamp();
  BEGIN
    UPDATE res_partner p SET active = false FROM pm_map m WHERE p.id = m.old_id;
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE 'arhivate % fișe în % s', n, round(extract(epoch from clock_timestamp() - t0), 1);
  END$$;
\else
  DO $$
  DECLARE n bigint; t0 timestamptz := clock_timestamp();
  BEGIN
    DELETE FROM res_partner p USING pm_map m WHERE p.id = m.old_id;
    GET DIAGNOSTICS n = ROW_COUNT;
    RAISE NOTICE 'șterse % fișe (FK ACTIVE) în % s', n, round(extract(epoch from clock_timestamp() - t0), 1);
  END$$;
\endif

\echo ''
\echo '== Verificare imediată: referințe rămase către fișele absorbite =='
-- Trebuie să fie 0 pe toate liniile. La mod_stergere='stergere' baza ar fi refuzat
-- oricum ștergerea; verificarea contează mai ales pentru legăturile polimorfe,
-- care NU au FK și deci nu sunt protejate de bază.
SELECT 'mail_activity'  AS unde, count(*) AS ramase FROM mail_activity  WHERE res_model = 'res.partner' AND res_id IN (SELECT old_id FROM pm_map)
UNION ALL SELECT 'ir_attachment',  count(*) FROM ir_attachment  WHERE res_model = 'res.partner' AND res_id IN (SELECT old_id FROM pm_map)
UNION ALL SELECT 'mail_message',   count(*) FROM mail_message   WHERE model     = 'res.partner' AND res_id IN (SELECT old_id FROM pm_map)
UNION ALL SELECT 'mail_followers', count(*) FROM mail_followers WHERE res_model = 'res.partner' AND res_id IN (SELECT old_id FROM pm_map)
UNION ALL SELECT 'ir_model_data',  count(*) FROM ir_model_data  WHERE model     = 'res.partner' AND res_id IN (SELECT old_id FROM pm_map);

\if :do_apply
  \echo ''
  \echo '>>> COMMIT — modificările se aplică'
  COMMIT;
\else
  \echo ''
  \echo '>>> SIMULARE — ROLLBACK, nimic nu s-a schimbat. Rulează cu -v do_apply=1 pentru a aplica.'
  ROLLBACK;
\endif
