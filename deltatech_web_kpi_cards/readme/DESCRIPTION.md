A technical module: a band of KPI cards that other modules put above their backend views, and the
binding that makes a click on a card activate the matching search filter.

- **One look for every dashboard** — a card shows a number (or amounts, one line per currency), a
  label, an icon and an accent colour; a card at zero stays coloured, dimmed; the active card is
  outlined. The colours are Odoo's own theme variables, so the cards follow the light and the dark
  mode of the backend.
- **A figure followed over time** — a card can also show its change against the previous period
  (green up, red down), a progress bar towards a target and a trend line; each is drawn only when
  the card gives it.
- **A click is a filter** — `useKpiCardFilters` activates the card's filter, drops the filters of
  the other cards so that two cards never add up, and clears the filter on a second click. The
  user's own filters are kept.
- **Nothing to configure** — the module adds no model, menu or data. It does nothing on its own:
  it is installed as a dependency of the modules that show cards.
