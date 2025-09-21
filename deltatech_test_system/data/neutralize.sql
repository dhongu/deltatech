INSERT INTO ir_config_parameter (key, value)
VALUES ('database.is_neutralized', 'True')
ON CONFLICT (key) DO UPDATE
SET value = 'True';
