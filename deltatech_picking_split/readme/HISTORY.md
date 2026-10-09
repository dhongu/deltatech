## 19.0.1.0.3 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.2 (2026-10-08)

- Fixed PICKSPLIT-002: the manual backorder wizard checked the kept quantity
  only in the form. Through RPC or a stale wizard, a kept quantity above the
  demand raised the demand of the original move and created a backorder with a
  negative quantity. The wizard now refuses, before changing anything, a kept
  quantity below zero or above the current demand of the move, a move that no
  longer belongs to the transfer, and a transfer already done or cancelled.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
