-- =============================================================================
-- 02 — Construiește maparea de unificare (old_id -> master_id) + snapshot de control
-- =============================================================================
-- Nu modifică date de business. Creează doar tabelele de lucru:
--   pm_group      — grupurile de duplicate pe CUI, cu categoria
--   pm_map        — fișele de absorbit și masterul lor (lotul curent)
--   pm_snapshot   — totalurile pe grup ÎNAINTE de unificare (pentru verificarea din 04)
--
-- Reguli de grupare: companii active, cu CUI normalizat (fără spații/punctuație),
-- grupuri cu cel puțin 2 membri.
--
-- Master = fața cu cele mai multe facturi, apoi cele mai multe comenzi,
--          apoi cea mai veche, apoi cel mai mic id (determinist).
--
-- Categorii:
--   A  o singură față are documente, restul sunt complet goale
--   B  documente doar pe o față (restul au cel mult date de contact)
--   C  facturi pe mai multe fețe
--   D  sold nereconciliat pe mai multe fețe
-- Lotul automat = A + B. C și D se tratează separat, cu contabilitatea.
--
-- Rulare:
--   psql -d <bd> -v categorii="'A','B'" -v limita_grupuri=200 -f 02_build_map.sql
-- Parametri (opționali, cu valori implicite mai jos):
--   categorii       — ce categorii intră în lot
--   limita_grupuri  — câte grupuri în lotul curent (0 = toate)
-- =============================================================================
\timing on
\set ON_ERROR_STOP on
\if :{?categorii}      \else \set categorii "'A','B'" \endif
\if :{?limita_grupuri} \else \set limita_grupuri 200  \endif

BEGIN;

-- 1) Fișele candidate, cu volumetria documentelor pe fiecare
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
  (SELECT count(*) FROM account_move m  WHERE m.partner_id = n.id AND m.move_type <> 'entry')          AS facturi,
  (SELECT count(*) FROM sale_order s    WHERE s.partner_id = n.id)                                      AS comenzi_v,
  (SELECT count(*) FROM purchase_order o WHERE o.partner_id = n.id)                                     AS comenzi_a,
  (SELECT count(*) FROM stock_picking k WHERE k.partner_id = n.id)                                      AS livrari,
  (SELECT count(*) FROM res_partner c   WHERE c.parent_id = n.id)                                       AS copii,
  (SELECT count(*) FROM sale_order s    WHERE s.partner_shipping_id = n.id OR s.partner_invoice_id = n.id) AS adresa_pe_comenzi,
  (SELECT count(*) FROM res_users u     WHERE u.partner_id = n.id)                                      AS useri,
  (SELECT count(*) FROM res_company k   WHERE k.partner_id = n.id)                                      AS e_companie_proprie,
  COALESCE((SELECT round(sum(l.balance)::numeric, 2)
            FROM account_move_line l
            JOIN account_account a ON a.id = l.account_id
            JOIN account_move mv   ON mv.id = l.move_id
           WHERE l.partner_id = n.id AND mv.state = 'posted' AND a.reconcile AND NOT l.reconciled), 0) AS sold
FROM norm n JOIN grp g ON g.vat_n = n.vat_n;
CREATE INDEX ON pm_face(vat_n);
CREATE UNIQUE INDEX ON pm_face(id);
ANALYZE pm_face;

-- 2) Clasificarea grupurilor + gărzile de excludere
DROP TABLE IF EXISTS pm_group CASCADE;
CREATE TABLE pm_group AS
WITH g AS (
  SELECT vat_n,
         count(*) AS membri,
         count(*) FILTER (WHERE facturi > 0)                                                    AS cu_facturi,
         count(*) FILTER (WHERE facturi + comenzi_v + comenzi_a + livrari
                              + copii + adresa_pe_comenzi + useri = 0)                          AS goi,
         count(*) FILTER (WHERE sold <> 0)                                                      AS cu_sold,
         count(*) FILTER (WHERE useri > 0)                                                      AS cu_useri,
         sum(e_companie_proprie)                                                                AS companii_proprii,
         -- denumiri divergente: prefixele numelor sunt toate distincte
         count(DISTINCT lower(left(regexp_replace(name, '[^[:alnum:] ]', '', 'g'), 6))) AS prefixe_nume
  FROM pm_face GROUP BY vat_n
)
SELECT vat_n, membri, cu_facturi, goi, cu_sold, cu_useri, companii_proprii, prefixe_nume,
  CASE
    WHEN goi = membri - 1 AND cu_facturi <= 1 THEN 'A'
    WHEN cu_facturi <= 1                      THEN 'B'
    WHEN cu_sold > 1                          THEN 'D'
    ELSE                                           'C'
  END AS categorie,
  -- Motivul pentru care grupul NU intră în lotul automat (NULL = eligibil)
  CASE
    WHEN companii_proprii > 0 THEN 'contine compania proprie'
    WHEN cu_useri > 1         THEN 'mai multe fete cu user portal'
    WHEN prefixe_nume = membri THEN 'denumiri divergente - revizuire manuala'
  END AS blocaj
FROM g;
CREATE UNIQUE INDEX ON pm_group(vat_n);
ANALYZE pm_group;

-- 3) Maparea lotului curent
DROP TABLE IF EXISTS pm_map CASCADE;
CREATE TABLE pm_map AS
WITH eligibil AS (
  SELECT vat_n FROM pm_group
  WHERE categorie IN (:categorii) AND blocaj IS NULL
  ORDER BY vat_n
  LIMIT CASE WHEN :limita_grupuri > 0 THEN :limita_grupuri ELSE NULL END
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
ANALYZE pm_map;

-- Gardă: un master nu poate fi el însuși absorbit în alt grup (lanț de unificare)
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pm_map m WHERE EXISTS (SELECT 1 FROM pm_map x WHERE x.old_id = m.master_id);
  IF n > 0 THEN
    RAISE EXCEPTION 'Lot inconsistent: % fișe au ca master un partener care e el însuși absorbit', n;
  END IF;
END$$;

-- 4) Snapshot de control: totalurile pe grup ÎNAINTE de unificare.
--    După merge, masterul trebuie să aibă exact aceste valori (nimic pierdut, nimic dublat).
DROP TABLE IF EXISTS pm_snapshot CASCADE;
CREATE TABLE pm_snapshot AS
SELECT m.master_id,
       count(*) + 1                          AS fise_in_grup,
       sum(f.facturi)   + mf.facturi         AS facturi_asteptate,
       sum(f.comenzi_v) + mf.comenzi_v       AS comenzi_v_asteptate,
       sum(f.comenzi_a) + mf.comenzi_a       AS comenzi_a_asteptate,
       sum(f.livrari)   + mf.livrari         AS livrari_asteptate,
       round(sum(f.sold) + mf.sold, 2)       AS sold_asteptat
FROM pm_map m
JOIN pm_face f  ON f.id = m.old_id
JOIN pm_face mf ON mf.id = m.master_id
GROUP BY m.master_id, mf.facturi, mf.comenzi_v, mf.comenzi_a, mf.livrari, mf.sold;
CREATE UNIQUE INDEX ON pm_snapshot(master_id);

COMMIT;

\echo ''
\echo '== Clasificarea completă a grupurilor =='
SELECT categorie, coalesce(blocaj, '(eligibil)') AS stare,
       count(*) AS grupuri, sum(membri) - count(*) AS fise_de_absorbit
FROM pm_group GROUP BY 1, 2 ORDER BY 1, 2;

\echo ''
\echo '== Lotul curent =='
SELECT count(DISTINCT master_id) AS grupuri, count(*) AS fise_de_absorbit FROM pm_map;

\echo ''
\echo '== Eșantion (10 grupuri din lot) =='
SELECT m.vat_n, m.master_id, f.name AS master, m.old_id, o.name AS absorbit,
       o.facturi, o.comenzi_v, o.sold
FROM pm_map m
JOIN pm_face f ON f.id = m.master_id
JOIN pm_face o ON o.id = m.old_id
WHERE m.vat_n IN (SELECT DISTINCT vat_n FROM pm_map ORDER BY vat_n LIMIT 10)
ORDER BY m.vat_n, m.old_id;
