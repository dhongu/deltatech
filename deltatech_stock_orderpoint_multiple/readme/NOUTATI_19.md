# Ce e nou în 19.0 — Cantitate multiplă la regulile de reaprovizionare

**Modul nou în 19.0.**

## Ce aduce
- **Readuce rotunjirea la un multiplu pe regulile de reaprovizionare**, câmp pe care Odoo l-a eliminat la trecerea la versiunea 19.0. Pentru companiile care comandă în paleți, baxuri sau multipli de ambalare, propunerile de reaprovizionare rămân realizabile.
- **Regula nu se blochează niciodată la zero.** În Odoo <= 18.0, dacă necesarul era mai mic decât multiplul iar regula avea un plafon, rotunjirea în jos dădea 0 și regula nu mai comanda nimic, la nesfârșit. Aici se comandă un multiplu întreg.
