For a module developer:

1. Give the view the js class: `js_class="side_panel_kanban"` on a `<kanban>`, or
   `js_class="side_panel_list"` on a `<list>`.
2. Define the form the panel shows (a form view of the same model) and put its xml id in the
   context of the action: `{'side_panel_view_ref': 'my_module.view_my_model_form_quick'}`. Without
   it, the panel shows the default form view of the model.
3. To switch the panel off for an action, add `'disable_side_panel': True` to its context.

The demo data of this module has a working example on contacts: open the action
*Contacts with side panel (demo)* (`deltatech_web_side_panel.action_demo_partners`).

For the user: click a card or a row to see the record on the right. Use the arrows in the header of
the panel to move through the records, the arrow-out button, or a double click on the card or on the row, to open the full form and the cross to
close the panel.
To change the width of the panel, drag the handle on its left edge (or focus it and use the left and
right arrow keys); a double click on the handle restores the default width. The chosen width is
remembered in the browser.

Select a record in a kanban card to see it in the panel:

![Kanban view with the selected card highlighted and its form in the side panel](static/description/en/01_kanban_cu_panou.png)

The list view uses the same panel and the same behaviour; the arrows in the header move to the
previous or the next record, and the arrow-out button opens the full form:

![List view with the selected row highlighted and its form in the side panel](static/description/en/02_lista_cu_panou.png)

The handle on the left edge of the panel changes its width (drag it, or use the arrow keys):

![Kanban view with a wider side panel and the resize handle highlighted](static/description/en/03_redimensionare_panou.png)
