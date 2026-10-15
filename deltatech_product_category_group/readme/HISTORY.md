## 20.0.1.0.6 (2026-10-15)

- `responsible_determination`: the candidates are now only active internal users (not portal) with the Inventory user group who can work in the company of the transfer; before, any member of the category group was a candidate. The number of "Ready" transfers used for balancing counts only the transfers of the same company. If no candidate is eligible the transfer is left unassigned. The "Responsible" button on the transfer list is restricted to Inventory managers.
- `responsible_determination` takes the categories from the moves (not cancelled) instead of the move lines: in a partially reserved transfer the unreserved moves were ignored when choosing the user group.
- Tests added for each case; the list-view arch check accepts bytes as well as text.

## 19.0.1.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
