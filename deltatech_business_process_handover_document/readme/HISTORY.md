## 20.0.0.0.7 (2026-10-16)

Migration to 20.0:

- The report template prints its values with `t-out` (server-side `t-esc` is ignored in 20).
- The computed `development_ids` field is labelled "Project Developments": it had the same
  label as `count_developments` of `deltatech_business_process` (registry warning).
- The paper format file had a stray character after the record; removed.
- New test that renders the handover document.

## 19.0.0.0.7 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.0.0.6 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
