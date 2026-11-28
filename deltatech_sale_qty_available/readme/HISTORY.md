## 19.0.1.0.6 (2026-11-28)

- Fix "Is ready" on draft/sent sale orders with the "all at once" shipping policy: the demand of several lines of the same product is now summed, so the same stock is no longer counted for each line (10 in stock and two lines of 6 no longer make the order ready).

## 19.0.1.0.5 (2026-11-11)

- Apps Store page: a fuller description (what the module does, the problem it solves, its main functions, dependencies and limits). No change in behavior.

## 19.0.1.0.4 (2026-10-02)

- Fix the "Is ready" filter on sale orders: it returned exactly the orders that are not ready (the ORM sends the `in` operator, the search method only handled `=`). `=`, `!=`, `in` and `not in` are now handled; the tests check the result.

## 19.0.1.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
