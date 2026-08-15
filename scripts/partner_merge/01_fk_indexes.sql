-- =============================================================================
-- 01 — Indexuri pe coloanele FK care referă res_partner
-- =============================================================================
-- De ce: res_partner e referit de ~158 de coloane FK, din care ~77 nu au index.
-- La FIECARE rând șters din res_partner, PostgreSQL verifică fiecare constrângere;
-- fără index verificarea e o scanare secvențială completă (măsurat: 3.180 MB
-- scanate per rând). De aici impresia că ștergerea/unificarea „nu se mai termină"
-- și tentația de a dezactiva FK-urile cu session_replication_role = replica.
--
-- Măsurat pe o bază de producție (5.624 fișe absorbite):
--   fără indexuri : DELETE > 8 min, întrerupt fără să termine
--   cu indexuri   : DELETE 178 s, cu FK ACTIVE
--
-- CONCURRENTLY => nu ia lock de scriere, se poate rula în timpul programului.
-- NU poate rula într-o tranzacție, de aceea acest fișier e separat și NU are BEGIN.
-- Dacă un index rămâne INVALID (întrerupere), vezi verificarea de la final.
--
-- Rulare:
--   psql -d <bd> -f 01_fk_indexes.sql
-- Idempotent: se poate relua oricând.
-- =============================================================================
\timing on
\set ON_ERROR_STOP on

\echo '== Coloane FK spre res_partner fără index (înainte) =='
SELECT count(*) AS fara_index,
       pg_size_pretty(sum(pg_relation_size(conrelid))) AS spatiu_scanat_per_stergere
FROM (
  SELECT c.conrelid, a.attnum
  FROM pg_constraint c
  JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
  WHERE c.contype = 'f' AND c.confrelid = 'res_partner'::regclass
    AND c.conrelid::regclass::text <> 'res_partner'
) fk
WHERE NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid = fk.conrelid AND fk.attnum = i.indkey[0]);

\echo '== Creare indexuri lipsă (CONCURRENTLY) =='
SELECT format(
         'CREATE INDEX CONCURRENTLY IF NOT EXISTS %I ON %s (%I);',
         left('ix_pfk_' || replace(tbl, '.', '_') || '_' || col, 63), tbl, col)
FROM (
  SELECT c.conrelid::regclass::text AS tbl, a.attname AS col, c.conrelid, a.attnum
  FROM pg_constraint c
  JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
  WHERE c.contype = 'f' AND c.confrelid = 'res_partner'::regclass
    AND c.conrelid::regclass::text <> 'res_partner'
) fk
WHERE NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid = fk.conrelid AND fk.attnum = i.indkey[0])
ORDER BY pg_relation_size(conrelid) DESC
\gexec

\echo '== Indexuri INVALID (create parțial, de recreat) =='
-- CREATE INDEX CONCURRENTLY întrerupt lasă un index invalid, care ocupă spațiu
-- și NU e folosit. Dacă apar rânduri aici: DROP INDEX <nume>; apoi reia scriptul.
SELECT c.relname AS index_invalid
FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
WHERE NOT i.indisvalid AND c.relnamespace = 'public'::regnamespace;

\echo '== Verificare finală =='
SELECT count(*) AS coloane_fk_ramase_fara_index
FROM (
  SELECT c.conrelid, a.attnum
  FROM pg_constraint c
  JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
  WHERE c.contype = 'f' AND c.confrelid = 'res_partner'::regclass
    AND c.conrelid::regclass::text <> 'res_partner'
) fk
WHERE NOT EXISTS (SELECT 1 FROM pg_index i WHERE i.indrelid = fk.conrelid AND fk.attnum = i.indkey[0]);
