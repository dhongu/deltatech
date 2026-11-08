1. Install the module, or on Odoo Online import the zip from **Apps > Import Module**
   (Custom plan, developer mode), then reload the page. There is nothing to configure.
2. Open any list, for example **Contacts > Contacts** in the list view. Press the mouse button at
   the start of a value (an email, a phone, a reference), drag to its end and release: the text
   stays selected and the record does not open. Copy it with Ctrl+C.

   ![Contacts list view: in the row TEST Northwind Builders Ltd the email office@northwind.test is selected and the list is still displayed](static/description/en/01_selectare_text_lista.png)

3. Click a row without selecting text: the record opens as usual.

   ![The form of TEST Northwind Builders Ltd, opened by a plain click on its row](static/description/en/02_clic_deschide_inregistrarea.png)

The module also fixes the save of a form after an unsaved one2many line was deleted twice (for
example with Enter pressed twice on its trash icon), which failed with a `virtual_N` error. In the
dark theme, it removes the light background of images in forms and kanban views.
