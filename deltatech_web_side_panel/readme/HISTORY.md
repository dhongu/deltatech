## 19.0.1.2.0 (2026-11-13)

- A double click on a card or on a row opens the full form of that record. A single click still
  selects it and shows it in the panel. Buttons, links and fields inside a card or a row keep their
  own behaviour, and on a small screen, where the panel is off, a click opens the form as before.

## 19.0.1.1.1 (2026-11-13)

- The form of the panel follows the width of the panel on a wide window. On a window of 1500px or
  more the form sheet kept the width of the window (up to 1500px) and overflowed the panel: the
  right-hand fields were cut off and resizing the panel changed nothing in the form. The sheet and
  the levels above it may now shrink to the panel.

## 19.0.1.1.0 (2026-11-13)

- The side panel can be resized: drag the handle on its left edge (or use the arrow keys on it,
  Home and End for the limits). The width stays between 300 px and 70% of the content area, a
  double click on the handle restores the default width, and the chosen width is remembered in the
  browser for every view that uses the panel. On a wide window (extra-large and up) the form sheet
  now follows the width of the panel instead of keeping the width of its content.

## 19.0.1.0.0 (2026-11-13)

- First release: a side panel with the form of the selected record, for kanban (`side_panel_kanban`)
  and list (`side_panel_list`) views. A click selects the record, the panel moves between records,
  opens the full form, refreshes and closes. The form comes from the action context key
  `side_panel_view_ref`.
