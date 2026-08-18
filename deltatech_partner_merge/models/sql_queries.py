"""Interogările folosite de unificarea în masă.

Provin din `scripts/partner_merge/*.sql`, care rămân varianta rulabilă direct din
psql. Aici sunt aceleași interogări, fără meta-comenzile psql (\\gexec, \\if,
variabilele -v) — acelea sunt înlocuite de parametri și de logica din
partner_merge_batch.py.

Tabelele de lucru păstrează numele din scripturi (pm_face, pm_group, pm_map,
pm_snapshot), ca un lot pregătit din interfață să poată fi inspectat din psql.
"""

# --- pasul 1: indexuri pe coloanele FK care referă res_partner ----------------
# În modul se creează FĂRĂ CONCURRENTLY: rulăm în tranzacția Odoo, unde
# CONCURRENTLY nu e permis. Lock-ul e de ordinul secundelor pe tabelele mari.
# Pentru instanțe unde nici atât nu e acceptabil, rulează 01_fk_indexes.sql din
# psql înainte, care folosește CONCURRENTLY.
FK_COLUMNS_WITHOUT_INDEX = """
    SELECT c.conrelid::regclass::text AS tbl, a.attname AS col,
           pg_relation_size(c.conrelid) AS tbl_size
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
    WHERE c.contype = 'f' AND c.confrelid = 'res_partner'::regclass
      AND c.conrelid::regclass::text <> 'res_partner'
      AND NOT EXISTS (
        SELECT 1 FROM pg_index i
         WHERE i.indrelid = c.conrelid AND a.attnum = i.indkey[0])
    ORDER BY pg_relation_size(c.conrelid) DESC
"""

# --- pasul 2: candidații, cu volumetria documentelor -------------------------
# Sub-interogările pe tabele care pot lipsi (modul neinstalat) sunt protejate cu
# to_regclass, ca modulul să depindă doar de `base`.
BUILD_FACE = """
    DROP TABLE IF EXISTS pm_face CASCADE;
    CREATE TABLE pm_face AS
    WITH norm AS (
      SELECT id, name, create_date, company_registry,
             upper(regexp_replace(vat, '[^0-9A-Za-z]', '', 'g')) AS vat_n
      FROM res_partner
      WHERE active AND is_company AND vat IS NOT NULL AND vat <> ''
    ), grp AS (
      SELECT vat_n FROM norm GROUP BY vat_n HAVING count(*) > 1
    )
    SELECT n.vat_n, n.id, n.name, n.create_date, n.company_registry,
      {facturi} AS facturi, {comenzi_v} AS comenzi_v, {comenzi_a} AS comenzi_a,
      {livrari} AS livrari,
      (SELECT count(*) FROM res_partner c WHERE c.parent_id = n.id) AS copii,
      {adresa} AS adresa_pe_comenzi,
      (SELECT count(*) FROM res_users u WHERE u.partner_id = n.id) AS useri,
      (SELECT count(*) FROM res_company k WHERE k.partner_id = n.id) AS e_companie_proprie,
      {sold} AS sold
    FROM norm n JOIN grp g ON g.vat_n = n.vat_n;
    CREATE INDEX ON pm_face(vat_n);
    CREATE UNIQUE INDEX ON pm_face(id);
"""
# fragmentele condiționale, alese în funcție de tabelele care există
FACE_PARTS = {
    "facturi": (
        "account_move",
        "(SELECT count(*) FROM account_move m WHERE m.partner_id = n.id AND m.move_type <> 'entry')",
    ),
    "comenzi_v": ("sale_order", "(SELECT count(*) FROM sale_order s WHERE s.partner_id = n.id)"),
    "comenzi_a": ("purchase_order", "(SELECT count(*) FROM purchase_order o WHERE o.partner_id = n.id)"),
    "livrari": ("stock_picking", "(SELECT count(*) FROM stock_picking k WHERE k.partner_id = n.id)"),
    "adresa": (
        "sale_order",
        "(SELECT count(*) FROM sale_order s WHERE s.partner_shipping_id = n.id OR s.partner_invoice_id = n.id)",
    ),
    "sold": (
        "account_move_line",
        "COALESCE((SELECT round(sum(l.balance)::numeric, 2) FROM account_move_line l "
        "JOIN account_account a ON a.id = l.account_id JOIN account_move mv ON mv.id = l.move_id "
        "WHERE l.partner_id = n.id AND mv.state = 'posted' AND a.reconcile AND NOT l.reconciled), 0)",
    ),
}

BUILD_GROUP = """
    DROP TABLE IF EXISTS pm_group CASCADE;
    CREATE TABLE pm_group AS
    WITH g AS (
      SELECT vat_n,
             count(*) AS membri,
             count(*) FILTER (WHERE facturi > 0) AS cu_facturi,
             count(*) FILTER (WHERE facturi + comenzi_v + comenzi_a + livrari
                                  + copii + adresa_pe_comenzi + useri = 0) AS goi,
             count(*) FILTER (WHERE sold <> 0) AS cu_sold,
             count(*) FILTER (WHERE useri > 0) AS cu_useri,
             sum(e_companie_proprie) AS companii_proprii,
             count(DISTINCT lower(left(regexp_replace(name, '[^[:alnum:] ]', '', 'g'), 6))) AS prefixe_nume
      FROM pm_face GROUP BY vat_n
    )
    SELECT vat_n, membri, cu_facturi, goi, cu_sold, cu_useri, companii_proprii, prefixe_nume,
      CASE WHEN goi = membri - 1 AND cu_facturi <= 1 THEN 'A'
           WHEN cu_facturi <= 1                      THEN 'B'
           WHEN cu_sold > 1                          THEN 'D'
           ELSE                                           'C' END AS categorie,
      CASE WHEN companii_proprii > 0  THEN 'company'
           WHEN cu_useri > 1          THEN 'portal_users'
           WHEN prefixe_nume = membri THEN 'diverging_names' END AS blocaj
    FROM g;
    CREATE UNIQUE INDEX ON pm_group(vat_n);
"""

BUILD_MAP = """
    DROP TABLE IF EXISTS pm_map CASCADE;
    CREATE TABLE pm_map AS
    WITH eligibil AS (
      SELECT vat_n FROM pm_group
      WHERE categorie = ANY(%s) AND blocaj IS NULL
      ORDER BY vat_n
      LIMIT %s
    ), master AS (
      SELECT DISTINCT ON (f.vat_n) f.vat_n, f.id AS master_id
      FROM pm_face f JOIN eligibil e ON e.vat_n = f.vat_n
      ORDER BY f.vat_n, f.facturi DESC, f.comenzi_v DESC, f.create_date ASC, f.id ASC
    )
    SELECT f.vat_n, f.id AS old_id, m.master_id
    FROM pm_face f JOIN master m ON m.vat_n = f.vat_n
    WHERE f.id <> m.master_id;
    CREATE UNIQUE INDEX ON pm_map(old_id);
    CREATE INDEX ON pm_map(master_id);
"""

# un master nu poate fi el însuși absorbit în alt grup
CHECK_NO_CHAIN = """
    SELECT count(*) FROM pm_map m WHERE EXISTS (SELECT 1 FROM pm_map x WHERE x.old_id = m.master_id)
"""

BUILD_SNAPSHOT = """
    DROP TABLE IF EXISTS pm_snapshot CASCADE;
    CREATE TABLE pm_snapshot AS
    SELECT m.master_id,
           count(*) + 1                      AS fise_in_grup,
           sum(f.facturi)   + mf.facturi     AS facturi_asteptate,
           sum(f.comenzi_v) + mf.comenzi_v   AS comenzi_v_asteptate,
           sum(f.comenzi_a) + mf.comenzi_a   AS comenzi_a_asteptate,
           sum(f.livrari)   + mf.livrari     AS livrari_asteptate,
           round(sum(f.sold) + mf.sold, 2)   AS sold_asteptat,
           string_agg(DISTINCT f.name, ' | ') AS denumiri_absorbite
    FROM pm_map m
    JOIN pm_face f  ON f.id = m.old_id
    JOIN pm_face mf ON mf.id = m.master_id
    GROUP BY m.master_id, mf.facturi, mf.comenzi_v, mf.comenzi_a, mf.livrari, mf.sold;
    CREATE UNIQUE INDEX ON pm_snapshot(master_id);
"""

# --- pasul 3: dedup coliziuni unique ----------------------------------------
# Colapsează pe valoarea ȚINTĂ, nu comparând fișa absorbită cu masterul: două fișe
# din același grup se ciocnesc între ele după remap, fără ca masterul să fie implicat.
# `k IS NOT NULL` pe un ROW() e adevărat doar când toate câmpurile sunt non-null —
# obligatoriu, fiindcă NULL nu produce coliziune într-un index unique, dar
# PARTITION BY grupează toate NULL-urile la un loc.
UNIQUE_INDEXES_TO_DEDUPE = """
    SELECT c.relname AS tbl, i.indrelid,
           (SELECT array_agg(att.attname ORDER BY k.ord)
              FROM unnest(i.indkey::int[]) WITH ORDINALITY k(attnum, ord)
              JOIN pg_attribute att ON att.attrelid = i.indrelid AND att.attnum = k.attnum) AS cols,
           tgt.col AS remap_col
    FROM pg_index i
    JOIN pg_class c ON c.oid = i.indrelid AND c.relkind = 'r'
                   AND c.relnamespace = 'public'::regnamespace
    JOIN LATERAL (
      SELECT a.attname AS col
      FROM pg_attribute a
      WHERE a.attrelid = i.indrelid AND a.attnum > 0 AND NOT a.attisdropped
        AND ((%s = 'fk' AND EXISTS (
                SELECT 1 FROM pg_constraint fc
                JOIN pg_attribute fa ON fa.attrelid = fc.conrelid AND fa.attnum = ANY(fc.conkey)
                WHERE fc.contype = 'f' AND fc.confrelid = 'res_partner'::regclass
                  AND fc.conrelid = i.indrelid AND fa.attname = a.attname))
          OR (%s = 'poly' AND a.attname = 'res_id'
              AND EXISTS (SELECT 1 FROM pg_attribute a2 WHERE a2.attrelid = i.indrelid
                           AND a2.attname IN ('res_model', 'model') AND NOT a2.attisdropped)))
      LIMIT 1
    ) tgt ON true
    WHERE i.indisunique AND i.indisvalid AND i.indpred IS NULL
      AND c.relname <> 'res_partner'
      AND tgt.col = ANY (SELECT att.attname FROM unnest(i.indkey::int[]) k(attnum)
                          JOIN pg_attribute att ON att.attrelid = i.indrelid AND att.attnum = k.attnum)
"""

DEDUPE_ONE = """
    WITH t AS (
      SELECT x.ctid AS cid, ROW({key_expr}) AS k
      FROM {tbl} x LEFT JOIN pm_map m ON m.old_id = x.{remap_col}
      {where_cl}
    ), dup AS (
      SELECT cid, row_number() OVER (PARTITION BY k ORDER BY cid) AS rn
      FROM t
      WHERE k IS NOT NULL
        AND k IN (SELECT k FROM t WHERE k IS NOT NULL GROUP BY k HAVING count(*) > 1)
    )
    DELETE FROM {tbl} WHERE ctid IN (SELECT cid FROM dup WHERE rn > 1)
"""

# coloana care ține numele modelului, pentru tabelele polimorfe
POLY_MODEL_COL = """
    SELECT a2.attname FROM pg_attribute a2
     WHERE a2.attrelid = %s AND a2.attname IN ('res_model', 'model')
       AND NOT a2.attisdropped
     ORDER BY CASE a2.attname WHEN 'res_model' THEN 0 ELSE 1 END LIMIT 1
"""

# --- pasul 4: remap ---------------------------------------------------------
FK_COLUMNS_ALL = """
    SELECT c.conrelid::regclass::text AS tbl, a.attname AS col
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
    WHERE c.contype = 'f' AND c.confrelid = 'res_partner'::regclass
      AND c.conrelid::regclass::text <> 'res_partner'
"""
REMAP_FK = "UPDATE {tbl} t SET {col} = m.master_id FROM pm_map m WHERE t.{col} = m.old_id"
REMAP_PARENT = "UPDATE res_partner p SET parent_id = m.master_id FROM pm_map m WHERE p.parent_id = m.old_id"

# Odoo folosește DOUĂ convenții polimorfe: (res_model, res_id) pentru mail.activity,
# ir.attachment, mail.followers, rating.rating; dar (model, res_id) pentru mail.message
# și ir.model.data. Tratarea doar a primeia lasă chatterul agățat de fișe șterse.
POLY_TABLES = """
    SELECT t.table_name,
           (SELECT c.column_name FROM information_schema.columns c
             WHERE c.table_schema = 'public' AND c.table_name = t.table_name
               AND c.column_name IN ('res_model', 'model')
             ORDER BY CASE c.column_name WHEN 'res_model' THEN 0 ELSE 1 END LIMIT 1) AS model_col
    FROM information_schema.tables t
    WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
      AND EXISTS (SELECT 1 FROM information_schema.columns c
                   WHERE c.table_schema = 'public' AND c.table_name = t.table_name
                     AND c.column_name = 'res_id')
      AND EXISTS (SELECT 1 FROM information_schema.columns c
                   WHERE c.table_schema = 'public' AND c.table_name = t.table_name
                     AND c.column_name IN ('res_model', 'model')
                     AND c.data_type IN ('character varying', 'text'))
"""
REMAP_POLY = (
    "UPDATE {tbl} t SET res_id = m.master_id FROM pm_map m WHERE t.{model_col} = 'res.partner' AND t.res_id = m.old_id"
)

# --- pasul 5: completarea câmpurilor goale pe master ------------------------
FILL_FIELDS = ("email", "phone", "website", "street", "street2", "city", "zip", "function")
FILL_ONE = """
    UPDATE res_partner mst SET {col} = src.val
    FROM (
      SELECT DISTINCT ON (m.master_id) m.master_id, o.{col} AS val
      FROM pm_map m JOIN res_partner o ON o.id = m.old_id
      WHERE o.{col} IS NOT NULL AND o.{col} <> ''
      ORDER BY m.master_id, o.write_date DESC
    ) src
    WHERE mst.id = src.master_id AND (mst.{col} IS NULL OR mst.{col} = '')
"""

# --- pasul 6: ștergerea sau arhivarea --------------------------------------
DELETE_ABSORBED = "DELETE FROM res_partner p USING pm_map m WHERE p.id = m.old_id"
ARCHIVE_ABSORBED = "UPDATE res_partner p SET active = false FROM pm_map m WHERE p.id = m.old_id"

# --- verificări -------------------------------------------------------------
VERIFY_TOTALS = """
    WITH real AS (
      SELECT s.master_id,
        {facturi_m} AS facturi, {comenzi_v_m} AS comenzi_v, {sold_m} AS sold
      FROM pm_snapshot s
    )
    SELECT count(*) AS verificati,
           count(*) FILTER (WHERE r.facturi   <> s.facturi_asteptate)   AS ab_facturi,
           count(*) FILTER (WHERE r.comenzi_v <> s.comenzi_v_asteptate) AS ab_comenzi,
           count(*) FILTER (WHERE r.sold      <> s.sold_asteptat)       AS ab_sold
    FROM pm_snapshot s JOIN real r ON r.master_id = s.master_id
"""
