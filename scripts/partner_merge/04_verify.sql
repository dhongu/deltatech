-- =============================================================================
-- 04 — Verificarea de după unificare
-- =============================================================================
-- Compară situația reală a masterilor cu snapshotul luat în 02, ÎNAINTE de merge.
-- Regula: ce era răspândit pe fișele grupului trebuie să se regăsească integral
-- pe master — nimic pierdut, nimic dublat.
--
-- Rulare (după COMMIT-ul lui 03):
--   psql -d <bd> -f 04_verify.sql
-- =============================================================================
\timing on
\set ON_ERROR_STOP on

\echo '== A. Fișele absorbite mai există? (0 = șterse; >0 = rulat în mod arhivare) =='
SELECT count(*) FILTER (WHERE p.id IS NOT NULL)     AS inca_existente,
       count(*) FILTER (WHERE p.active)             AS inca_active
FROM pm_map m LEFT JOIN res_partner p ON p.id = m.old_id;

\echo ''
\echo '== B. Totaluri pe master: real vs. așteptat =='
WITH real AS (
  SELECT s.master_id,
    (SELECT count(*) FROM account_move mv WHERE mv.partner_id = s.master_id AND mv.move_type <> 'entry') AS facturi,
    (SELECT count(*) FROM sale_order so    WHERE so.partner_id = s.master_id)                             AS comenzi_v,
    (SELECT count(*) FROM purchase_order po WHERE po.partner_id = s.master_id)                            AS comenzi_a,
    (SELECT count(*) FROM stock_picking sp WHERE sp.partner_id = s.master_id)                             AS livrari,
    COALESCE((SELECT round(sum(l.balance)::numeric, 2)
              FROM account_move_line l
              JOIN account_account a ON a.id = l.account_id
              JOIN account_move mv   ON mv.id = l.move_id
             WHERE l.partner_id = s.master_id AND mv.state = 'posted' AND a.reconcile AND NOT l.reconciled), 0) AS sold
  FROM pm_snapshot s
)
SELECT count(*)                                                              AS masteri_verificati,
       count(*) FILTER (WHERE r.facturi   <> s.facturi_asteptate)            AS abateri_facturi,
       count(*) FILTER (WHERE r.comenzi_v <> s.comenzi_v_asteptate)          AS abateri_comenzi_v,
       count(*) FILTER (WHERE r.comenzi_a <> s.comenzi_a_asteptate)          AS abateri_comenzi_a,
       count(*) FILTER (WHERE r.livrari   <> s.livrari_asteptate)            AS abateri_livrari,
       count(*) FILTER (WHERE r.sold      <> s.sold_asteptat)                AS abateri_sold
FROM pm_snapshot s JOIN real r ON r.master_id = s.master_id;

\echo ''
\echo '== C. Detaliul abaterilor (trebuie să fie gol) =='
WITH real AS (
  SELECT s.master_id,
    (SELECT count(*) FROM account_move mv WHERE mv.partner_id = s.master_id AND mv.move_type <> 'entry') AS facturi,
    (SELECT count(*) FROM sale_order so    WHERE so.partner_id = s.master_id)                             AS comenzi_v,
    COALESCE((SELECT round(sum(l.balance)::numeric, 2)
              FROM account_move_line l
              JOIN account_account a ON a.id = l.account_id
              JOIN account_move mv   ON mv.id = l.move_id
             WHERE l.partner_id = s.master_id AND mv.state = 'posted' AND a.reconcile AND NOT l.reconciled), 0) AS sold
  FROM pm_snapshot s
)
SELECT s.master_id, p.name,
       s.facturi_asteptate, r.facturi,
       s.comenzi_v_asteptate, r.comenzi_v,
       s.sold_asteptat, r.sold
FROM pm_snapshot s
JOIN real r ON r.master_id = s.master_id
LEFT JOIN res_partner p ON p.id = s.master_id
WHERE r.facturi <> s.facturi_asteptate
   OR r.comenzi_v <> s.comenzi_v_asteptate
   OR r.sold <> s.sold_asteptat
ORDER BY 1 LIMIT 50;

\echo ''
\echo '== D. Orfani polimorfi ÎN TOATĂ BAZA (stare preexistentă, nu efectul acestui lot) =='
-- ATENȚIE la interpretare: numără orfanii din toată baza, inclusiv cei lăsați de ștergeri
-- anterioare făcute din interfață sau din alte scripturi. Efectul lotului curent se citește
-- din verificarea de la finalul lui 03, care filtrează pe pm_map. O valoare nenulă aici NU
-- înseamnă că unificarea a lăsat referințe în urmă.
SELECT 'mail_activity' AS unde, count(*) AS orfane FROM mail_activity WHERE res_model='res.partner' AND res_id NOT IN (SELECT id FROM res_partner)
UNION ALL SELECT 'ir_attachment', count(*) FROM ir_attachment WHERE res_model='res.partner' AND res_id NOT IN (SELECT id FROM res_partner)
UNION ALL SELECT 'mail_message',  count(*) FROM mail_message  WHERE model='res.partner'     AND res_id NOT IN (SELECT id FROM res_partner)
UNION ALL SELECT 'mail_followers',count(*) FROM mail_followers WHERE res_model='res.partner' AND res_id NOT IN (SELECT id FROM res_partner)
UNION ALL SELECT 'ir_model_data', count(*) FROM ir_model_data WHERE model='res.partner'      AND res_id NOT IN (SELECT id FROM res_partner);

\echo ''
\echo '== E. Masteri cu denumire suspectă (de corectat manual) =='
-- Masterul e ales după volumul de documente, NU după calitatea denumirii. Uneori
-- supraviețuiește fișa cu numele prost formatat (fără spații, sau chiar egal cu CUI-ul),
-- iar varianta corectă era pe o fișă absorbită. Nu afectează integritatea, dar se vede
-- în rapoarte și în documentele emise de aici înainte.
-- Pragul de lungime nu e suficient: „MayaVirágKft" are exact 12 caractere și scăpa,
-- deși e clar o denumire lipită la import. Semnalul mai bun e tranziția
-- minusculă -> MAJUSCULĂ într-un nume fără spații (CamelCase), indiferent de lungime.
SELECT p.id, p.name AS denumire_master, p.vat,
       CASE WHEN p.name ~ '^[A-Z]{0,2}[0-9]{4,}$'                     THEN 'denumirea e chiar CUI-ul'
            WHEN p.name !~ ' ' AND p.name ~ '[[:lower:]][[:upper:]]'  THEN 'cuvinte lipite (import prost)'
            WHEN p.name !~ ' ' AND length(p.name) > 8                 THEN 'fără spații'
       END AS motiv,
       s.denumiri_absorbite AS variante_absorbite
FROM pm_snapshot s JOIN res_partner p ON p.id = s.master_id
WHERE p.name ~ '^[A-Z]{0,2}[0-9]{4,}$'
   OR (p.name !~ ' ' AND (p.name ~ '[[:lower:]][[:upper:]]' OR length(p.name) > 8))
ORDER BY 1;

\echo ''
\echo '== F. Duplicate pe CUI rămase (progres) =='
SELECT count(*) AS grupuri_ramase, sum(n) - count(*) AS fise_inca_de_absorbit
FROM (SELECT count(*) AS n FROM res_partner
      WHERE active AND is_company AND vat IS NOT NULL AND vat <> ''
      GROUP BY upper(regexp_replace(vat, '[^0-9A-Za-z]', '', 'g')) HAVING count(*) > 1) t;
