-- A neutralized copy (odoo.sh staging / dev, `odoo-bin neutralize`) must not share the station
-- keys of production: an agent configured for production would also serve the copy, and an agent
-- configured for the copy would authenticate on production. New random keys (gen_random_uuid()
-- is cryptographically random), so each station of the copy needs its station.conf downloaded
-- again.
UPDATE deltatech_tc_station
   SET api_key = replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', '');

-- Jobs copied while queued were meant for production's stations (prints, scale readings,
-- queries): close them instead of running them a second time from the copy.
UPDATE deltatech_tc_job
   SET state = 'error',
       error = 'Not sent: the database was neutralized (copy of another database).'
 WHERE state IN ('pending', 'claimed');
