## 19.0.1.0.0 (2026-10-17)

- Migration to 19.0. The module stays an empty, obsolete compatibility shim (no models, views or data) that only depends on `deltatech_record_type`, so databases that still have it installed can upgrade cleanly; it can be uninstalled afterwards.
