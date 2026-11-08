1. Install the module, or on Odoo Online import the zip from **Apps > Import Module**
   (Custom plan, developer mode), then reload the page. There is nothing to configure.
2. Open **Contacts > Contacts**, click **New** and type a company name that does not exist yet
   in the company field under the name (building icon, placeholder **Company Employer**). The
   dropdown no longer offers **Create "..."**: only **Create and edit...** is left. Every
   many2one field behaves the same way (customer, product, category, salesperson).

   ![New contact Jane Smith: Zz New Company Ltd is typed in the company field under the name and the dropdown shows a single option, Create and edit...](static/description/en/01_lista_fara_creare_rapida.png)

3. Click **Create and edit...**: the **Create Related Company** dialog opens with the typed name
   already filled in. Complete the address and tax ID, then click **Save**.

   ![Create Related Company dialog over the contact form, with the name Zz New Company Ltd prefilled and the Save and Discard buttons](static/description/en/02_formular_creare_si_editare.png)
