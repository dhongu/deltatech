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
