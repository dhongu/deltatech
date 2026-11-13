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
the panel to move through the records, the arrow-out button to open the full form and the cross to
close the panel.
