A technical module: a panel on the right of a kanban or a list that shows the form of the record
the user selected, without leaving the screen.

- **One click selects** — a click on a card or on a row shows the record in the panel and highlights
  it, instead of opening its full form. The panel has buttons to move to the previous or the next
  record, open the full form, refresh and close. A double click on a card or on a row opens the
  full form.
- **The form is yours** — the panel embeds a form view, read-only, so a module defines what the
  panel shows in XML (header, fields, notebook, buttons) and the usual widgets work.
- **Kanban and list, one behaviour** — the views `side_panel_kanban` and `side_panel_list` share the
  same panel and the same behaviour: a click selects the record in either view.
- **Resizable** — drag the handle on the left edge of the panel to change its width; the width is
  remembered in the browser.
- **Small screens keep the usual views** — below the extra-large breakpoint the click opens the form
  as before.
