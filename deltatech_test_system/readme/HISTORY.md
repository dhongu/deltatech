# Changelog

## 19.0.0.0.9 (2026-08-15)

- Fix: added the missing `base_setup` dependency. The settings view inherits
  `base_setup.res_config_settings_view_form`, so installing the module on a
  database without `base_setup` failed with `External ID not found`.
