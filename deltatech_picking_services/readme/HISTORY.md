## 20.0.1.0.2 (2026-10-08)

- Fixed PICKSERVICE-001: a stock user could search, read, change or delete the
  service lines of transfers belonging to companies they do not have access
  to. Service lines now carry the company of their transfer and follow a
  multi-company record rule.
- Service lines are deleted together with their transfer, instead of being
  left without transfer.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
